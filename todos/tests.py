import json

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from reporting.models import Company, Department, FollowUp, UserCompany, UserProfile
from .models import Todo, TodoAttachment, TodoLog


def make_user(username, role='salesman', company=None, can_use_ai=False):
    user = User.objects.create_user(username=username, password='TestPass123!')
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.role = role
    profile.company = company
    profile.can_use_ai = can_use_ai
    profile.save()
    return user


class ReactTasksApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='Tasks Company')
        self.other_company = UserCompany.objects.create(name='Other Company')
        self.user = make_user('tasks_user', company=self.company, can_use_ai=True)
        self.colleague = make_user('tasks_colleague', company=self.company)
        self.manager = make_user('tasks_manager', role='manager', company=self.company)
        self.admin = make_user('tasks_admin', role='admin', company=self.company)
        self.other_user = make_user('tasks_other', company=self.other_company)

        customer_company = Company.objects.create(name='업무 고객사', created_by=self.user)
        department = Department.objects.create(name='업무 연구실', company=customer_company, created_by=self.user)
        self.followup = FollowUp.objects.create(
            user=self.user,
            user_company=self.company,
            company=customer_company,
            department=department,
            customer_name='업무 고객',
        )

    def test_tasks_api_requires_login_json(self):
        response = self.client.get(reverse('reporting:tasks_api'))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'login_required')

    def test_navigation_api_returns_role_based_task_items(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('reporting:navigation_api'))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        item_ids = [item['id'] for item in payload['items']]
        self.assertIn('tasks', item_ids)
        self.assertNotIn('tasksManager', item_ids)
        self.assertIn('mail', item_ids)
        self.assertIn('ai', item_ids)

        self.client.force_login(self.manager)
        manager_response = self.client.get(reverse('reporting:navigation_api'))
        manager_ids = [item['id'] for item in manager_response.json()['items']]
        self.assertIn('tasks', manager_ids)
        self.assertIn('tasksManager', manager_ids)
        self.assertNotIn('mail', manager_ids)

    def test_create_self_task_and_list_my_tasks(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('reporting:tasks_create_api'),
            data=json.dumps({
                'title': '견적 후속 확인',
                'description': '다음 주 납기 확인',
                'dueDate': timezone.localdate().isoformat(),
                'expectedDuration': 30,
                'relatedClientId': self.followup.id,
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        task = Todo.objects.get(title='견적 후속 확인')
        self.assertEqual(task.created_by, self.user)
        self.assertIsNone(task.assigned_to)
        self.assertEqual(task.status, Todo.Status.ONGOING)
        self.assertEqual(task.related_client, self.followup)
        self.assertTrue(TodoLog.objects.filter(todo=task, action_type=TodoLog.ActionType.CREATED).exists())

        list_response = self.client.get(reverse('reporting:tasks_api'))
        my_tasks = list_response.json()['tasks']['my']
        self.assertEqual([item['id'] for item in my_tasks], [task.id])
        self.assertEqual(my_tasks[0]['relatedClient']['customer'], '업무 고객')

    def test_peer_request_same_company_and_status_flow(self):
        self.client.force_login(self.user)
        blocked = self.client.post(
            reverse('reporting:tasks_request_api'),
            data=json.dumps({
                'title': '타사 요청 차단',
                'assignedToId': self.other_user.id,
            }),
            content_type='application/json',
        )
        self.assertEqual(blocked.status_code, 403)

        response = self.client.post(
            reverse('reporting:tasks_request_api'),
            data=json.dumps({
                'title': '동료 확인 요청',
                'description': '메일 회신 부탁',
                'assignedToId': self.colleague.id,
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        task = Todo.objects.get(title='동료 확인 요청')
        self.assertEqual(task.status, Todo.Status.PENDING)
        self.assertEqual(task.requested_by, self.user)
        self.assertEqual(task.assigned_to, self.colleague)

        requester_done = self.client.post(
            reverse('reporting:tasks_status_api', args=[task.id]),
            data=json.dumps({'status': 'done'}),
            content_type='application/json',
        )
        self.assertEqual(requester_done.status_code, 403)

        self.client.force_login(self.colleague)
        received = self.client.get(reverse('reporting:tasks_api'))
        self.assertEqual([item['id'] for item in received.json()['tasks']['received']], [task.id])

        approve = self.client.post(
            reverse('reporting:tasks_status_api', args=[task.id]),
            data=json.dumps({'action': 'approve'}),
            content_type='application/json',
        )
        self.assertEqual(approve.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, Todo.Status.ONGOING)

        done = self.client.post(
            reverse('reporting:tasks_status_api', args=[task.id]),
            data=json.dumps({'status': 'done'}),
            content_type='application/json',
        )
        self.assertEqual(done.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, Todo.Status.DONE)
        self.assertIsNotNone(task.completed_at)

    def test_reject_peer_request_creates_requester_copy(self):
        task = Todo.objects.create(
            title='반려 테스트',
            created_by=self.user,
            assigned_to=self.colleague,
            requested_by=self.user,
            source_type=Todo.SourceType.PEER_REQUEST,
            status=Todo.Status.PENDING,
        )
        self.client.force_login(self.colleague)

        response = self.client.post(
            reverse('reporting:tasks_status_api', args=[task.id]),
            data=json.dumps({'action': 'reject', 'reason': '이번 주 불가'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, Todo.Status.REJECTED)
        self.assertEqual(
            Todo.objects.filter(title='반려 테스트', created_by=self.user, assigned_to__isnull=True).count(),
            1,
        )

    def test_manager_assign_scope_and_manager_status(self):
        self.client.force_login(self.user)
        forbidden = self.client.get(reverse('reporting:tasks_manager_api'))
        self.assertEqual(forbidden.status_code, 403)

        self.client.force_login(self.manager)
        response = self.client.post(
            reverse('reporting:tasks_manager_assign_api'),
            data=json.dumps({
                'title': '주간 핵심 고객 확인',
                'description': '핵심 고객 진행상황 점검',
                'assignedToIds': [self.colleague.id, self.other_user.id],
                'dueDate': timezone.localdate().isoformat(),
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.json()['tasks']), 1)
        task = Todo.objects.get(title='주간 핵심 고객 확인')
        self.assertEqual(task.requested_by, self.manager)
        self.assertEqual(task.assigned_to, self.colleague)
        self.assertEqual(task.source_type, Todo.SourceType.MANAGER_ASSIGN)

        manager_payload = self.client.get(reverse('reporting:tasks_manager_api')).json()
        self.assertEqual(manager_payload['metrics']['total'], 1)
        self.assertEqual(manager_payload['teamSummary'][0]['active'], 1)

        hold = self.client.post(
            reverse('reporting:tasks_manager_status_api', args=[task.id]),
            data=json.dumps({'status': 'on_hold'}),
            content_type='application/json',
        )
        self.assertEqual(hold.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, Todo.Status.ON_HOLD)

    def test_task_detail_api_returns_attachments_and_logs_with_scope(self):
        task = Todo.objects.create(
            title='상세 확인 업무',
            description='상세 본문',
            created_by=self.user,
            assigned_to=self.colleague,
            requested_by=self.user,
            source_type=Todo.SourceType.PEER_REQUEST,
            status=Todo.Status.PENDING,
            related_client=self.followup,
        )
        TodoLog.objects.create(todo=task, actor=self.user, action_type=TodoLog.ActionType.CREATED, message='생성 로그')
        attachment = TodoAttachment.objects.create(
            todo=task,
            file=SimpleUploadedFile('detail.txt', b'detail', content_type='text/plain'),
            filename='detail.txt',
            uploaded_by=self.user,
        )
        self.addCleanup(attachment.file.delete, False)

        self.client.force_login(self.colleague)
        response = self.client.get(reverse('reporting:tasks_detail_api', args=[task.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['task']['id'], task.id)
        self.assertEqual(payload['task']['detailHref'], f'/tasks/{task.id}/')
        self.assertEqual(payload['task']['relatedClient']['customer'], '업무 고객')
        self.assertEqual(payload['attachments'][0]['filename'], 'detail.txt')
        self.assertEqual(
            payload['attachments'][0]['downloadHref'],
            reverse('reporting:tasks_attachment_download_api', args=[attachment.id]),
        )
        self.assertEqual(payload['logs'][0]['message'], '생성 로그')
        self.assertTrue(payload['task']['canComment'])
        self.assertEqual(payload['task']['commentHref'], reverse('reporting:tasks_comment_api', args=[task.id]))

        self.client.force_login(self.other_user)
        forbidden = self.client.get(reverse('reporting:tasks_detail_api', args=[task.id]))
        self.assertEqual(forbidden.status_code, 403)

    def test_task_comment_api_allows_participants_and_same_company_manager(self):
        task = Todo.objects.create(
            title='댓글 확인 업무',
            description='댓글 본문',
            created_by=self.user,
            assigned_to=self.colleague,
            requested_by=self.user,
            source_type=Todo.SourceType.PEER_REQUEST,
            status=Todo.Status.ONGOING,
        )

        self.client.force_login(self.colleague)
        colleague_comment = self.client.post(
            reverse('reporting:tasks_comment_api', args=[task.id]),
            data=json.dumps({'message': '처리 진행 중입니다.'}),
            content_type='application/json',
        )
        self.assertEqual(colleague_comment.status_code, 200)
        self.assertEqual(colleague_comment.json()['message'], '댓글을 추가했습니다.')
        self.assertTrue(TodoLog.objects.filter(
            todo=task,
            actor=self.colleague,
            action_type=TodoLog.ActionType.COMMENTED,
            message='처리 진행 중입니다.',
        ).exists())

        self.client.force_login(self.manager)
        manager_comment = self.client.post(
            reverse('reporting:tasks_comment_api', args=[task.id]),
            data=json.dumps({'message': '마감 전에 공유해주세요.'}),
            content_type='application/json',
        )
        self.assertEqual(manager_comment.status_code, 200)
        self.assertFalse(manager_comment.json()['task']['canUpdate'])
        self.assertTrue(TodoLog.objects.filter(
            todo=task,
            actor=self.manager,
            action_type=TodoLog.ActionType.COMMENTED,
            message='마감 전에 공유해주세요.',
        ).exists())

        self.client.force_login(self.other_user)
        forbidden = self.client.post(
            reverse('reporting:tasks_comment_api', args=[task.id]),
            data=json.dumps({'message': '외부 댓글'}),
            content_type='application/json',
        )
        self.assertEqual(forbidden.status_code, 403)

    def test_task_comment_api_validates_message(self):
        task = Todo.objects.create(
            title='빈 댓글 확인',
            created_by=self.user,
            source_type=Todo.SourceType.SELF,
            status=Todo.Status.ONGOING,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:tasks_comment_api', args=[task.id]),
            data=json.dumps({'message': '  '}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], '댓글 내용을 입력하세요.')

    def test_task_attachment_download_api_is_protected_and_scoped(self):
        task = Todo.objects.create(
            title='다운로드 업무',
            description='첨부 보호',
            created_by=self.user,
            assigned_to=self.colleague,
            requested_by=self.user,
            source_type=Todo.SourceType.PEER_REQUEST,
            status=Todo.Status.ONGOING,
        )
        attachment = TodoAttachment.objects.create(
            todo=task,
            file=SimpleUploadedFile('task-download.txt', b'task file', content_type='text/plain'),
            filename='task-download.txt',
            uploaded_by=self.user,
        )
        self.addCleanup(attachment.file.delete, False)
        download_url = reverse('reporting:tasks_attachment_download_api', args=[attachment.id])

        anonymous_response = self.client.get(download_url)
        self.assertEqual(anonymous_response.status_code, 401)
        self.assertEqual(anonymous_response.json()['error'], 'login_required')

        self.client.force_login(self.other_user)
        forbidden_response = self.client.get(download_url)
        self.assertEqual(forbidden_response.status_code, 403)
        self.assertNotIn('attachment', forbidden_response.get('Content-Disposition', ''))

        self.client.force_login(self.colleague)
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response.get('Content-Disposition', ''))
        response.close()

    def test_task_update_delete_and_attachment_api_permissions(self):
        task = Todo.objects.create(
            title='수정할 업무',
            description='이전 내용',
            due_date=timezone.localdate(),
            created_by=self.user,
            source_type=Todo.SourceType.SELF,
            status=Todo.Status.ONGOING,
        )
        self.client.force_login(self.colleague)
        forbidden_update = self.client.post(
            reverse('reporting:tasks_update_api', args=[task.id]),
            data=json.dumps({'title': '권한 없음'}),
            content_type='application/json',
        )
        self.assertEqual(forbidden_update.status_code, 403)

        self.client.force_login(self.user)
        update = self.client.post(
            reverse('reporting:tasks_update_api', args=[task.id]),
            data=json.dumps({
                'title': '수정된 업무',
                'description': '새 내용',
                'expectedDuration': 60,
                'relatedClientId': self.followup.id,
            }),
            content_type='application/json',
        )
        self.assertEqual(update.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.title, '수정된 업무')
        self.assertEqual(task.expected_duration, 60)
        self.assertEqual(task.related_client, self.followup)

        upload = self.client.post(
            reverse('reporting:tasks_attachment_upload_api', args=[task.id]),
            data={'files': [SimpleUploadedFile('react-task.txt', b'react task', content_type='text/plain')]},
        )
        self.assertEqual(upload.status_code, 200)
        self.assertEqual(TodoAttachment.objects.filter(todo=task).count(), 1)
        self.assertEqual(upload.json()['attachments'][0]['filename'], 'react-task.txt')
        attachment = TodoAttachment.objects.get(todo=task)
        self.addCleanup(attachment.file.delete, False)
        self.assertEqual(
            upload.json()['attachments'][0]['downloadHref'],
            reverse('reporting:tasks_attachment_download_api', args=[attachment.id]),
        )

        delete = self.client.post(reverse('reporting:tasks_delete_api', args=[task.id]))
        self.assertEqual(delete.status_code, 200)
        self.assertFalse(Todo.objects.filter(id=task.id).exists())

    def test_legacy_todo_get_routes_redirect_to_react_and_post_fallback_remains(self):
        task = Todo.objects.create(
            title='legacy 업무',
            created_by=self.user,
            source_type=Todo.SourceType.SELF,
            status=Todo.Status.ONGOING,
        )
        self.client.force_login(self.user)

        redirects = [
            (reverse('todos:list'), '/tasks/'),
            (reverse('todos:my_list'), '/tasks/?tab=my'),
            (reverse('todos:received_list'), '/tasks/?tab=received'),
            (reverse('todos:requested_list'), '/tasks/?tab=requested'),
            (reverse('todos:create'), '/tasks/?create=1'),
            (reverse('todos:request_to_peer'), '/tasks/?mode=request'),
            (reverse('todos:detail', args=[task.id]), f'/tasks/{task.id}/'),
            (reverse('todos:edit', args=[task.id]), f'/tasks/{task.id}/?edit=1'),
            (reverse('todos:delete', args=[task.id]), f'/tasks/{task.id}/?delete=1'),
        ]
        for url, expected_location in redirects:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response['Location'], expected_location)

        create_response = self.client.post(
            reverse('todos:create'),
            data={'title': 'legacy POST fallback', 'description': '기존 폼 호환'},
        )
        self.assertEqual(create_response.status_code, 302)
        self.assertTrue(Todo.objects.filter(title='legacy POST fallback', created_by=self.user).exists())

    def test_legacy_manager_todo_get_routes_redirect_to_react(self):
        task = Todo.objects.create(
            title='legacy manager 업무',
            created_by=self.manager,
            assigned_to=self.colleague,
            requested_by=self.manager,
            source_type=Todo.SourceType.MANAGER_ASSIGN,
            status=Todo.Status.ONGOING,
        )
        self.client.force_login(self.manager)

        redirects = [
            (reverse('todos:manager_dashboard'), '/tasks/manager/'),
            (reverse('todos:manager_task_detail', args=[task.id]), f'/tasks/{task.id}/'),
            (reverse('todos:manager_workload'), '/tasks/manager/'),
        ]
        for url, expected_location in redirects:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response['Location'], expected_location)
