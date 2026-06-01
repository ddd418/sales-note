from decimal import Decimal

from django.db import migrations


def normalize_probability(value):
    if value is None:
        return None
    value = int(value)
    value = max(0, min(100, value))
    return max(0, min(100, ((value + 2) // 5) * 5))


def weighted_amount(amount, probability):
    return Decimal(str(amount or 0)) * Decimal(str(probability or 0)) / Decimal('100')


def normalize_probability_values(apps, schema_editor):
    Quote = apps.get_model('reporting', 'Quote')
    Schedule = apps.get_model('reporting', 'Schedule')
    OpportunityTracking = apps.get_model('reporting', 'OpportunityTracking')
    FunnelStage = apps.get_model('reporting', 'FunnelStage')

    quotes = []
    for quote in Quote.objects.all().only('id', 'probability', 'total_amount', 'weighted_revenue'):
        normalized = normalize_probability(quote.probability)
        if normalized != quote.probability:
            quote.probability = normalized
            quote.weighted_revenue = weighted_amount(quote.total_amount, normalized)
            quotes.append(quote)
    if quotes:
        Quote.objects.bulk_update(quotes, ['probability', 'weighted_revenue'])

    schedules = []
    for schedule in Schedule.objects.exclude(probability__isnull=True).only('id', 'probability'):
        normalized = normalize_probability(schedule.probability)
        if normalized != schedule.probability:
            schedule.probability = normalized
            schedules.append(schedule)
    if schedules:
        Schedule.objects.bulk_update(schedules, ['probability'])

    opportunities = []
    for opportunity in OpportunityTracking.objects.all().only('id', 'probability', 'expected_revenue', 'weighted_revenue'):
        normalized = normalize_probability(opportunity.probability)
        if normalized != opportunity.probability:
            opportunity.probability = normalized
            opportunity.weighted_revenue = weighted_amount(opportunity.expected_revenue, normalized)
            opportunities.append(opportunity)
    if opportunities:
        OpportunityTracking.objects.bulk_update(opportunities, ['probability', 'weighted_revenue'])

    stages = []
    for stage in FunnelStage.objects.all().only('id', 'default_probability'):
        normalized = normalize_probability(stage.default_probability)
        if normalized != stage.default_probability:
            stage.default_probability = normalized
            stages.append(stage)
    if stages:
        FunnelStage.objects.bulk_update(stages, ['default_probability'])


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0115_department_only_notes_schedules'),
    ]

    operations = [
        migrations.RunPython(normalize_probability_values, migrations.RunPython.noop),
    ]
