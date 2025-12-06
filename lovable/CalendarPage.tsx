import { useState } from "react";
import { ChevronLeft, ChevronRight, Plus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const events = [
  { id: 1, title: "테크솔루션 데모", date: "2024-01-22", type: "meeting" },
  { id: 2, title: "글로벌트레이딩 화상회의", date: "2024-01-22", type: "video" },
  { id: 3, title: "헬스케어 전화상담", date: "2024-01-23", type: "call" },
  { id: 4, title: "주간 영업회의", date: "2024-01-24", type: "meeting" },
  { id: 5, title: "에코그린 현장방문", date: "2024-01-25", type: "meeting" },
  { id: 6, title: "월말 마감", date: "2024-01-31", type: "task" },
];

const typeColors = {
  meeting: "bg-primary",
  video: "bg-chart-4",
  call: "bg-success",
  task: "bg-warning",
};

export default function CalendarPage() {
  const [currentDate, setCurrentDate] = useState(new Date(2024, 0, 1)); // January 2024

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const firstDayOfMonth = new Date(year, month, 1);
  const lastDayOfMonth = new Date(year, month + 1, 0);
  const startingDayOfWeek = firstDayOfMonth.getDay();
  const daysInMonth = lastDayOfMonth.getDate();

  const days = [];
  for (let i = 0; i < startingDayOfWeek; i++) {
    days.push(null);
  }
  for (let i = 1; i <= daysInMonth; i++) {
    days.push(i);
  }

  const prevMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1));
  };

  const nextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1));
  };

  const getEventsForDay = (day: number) => {
    const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    return events.filter(e => e.date === dateStr);
  };

  const monthNames = [
    "1월", "2월", "3월", "4월", "5월", "6월",
    "7월", "8월", "9월", "10월", "11월", "12월"
  ];

  const dayNames = ["일", "월", "화", "수", "목", "금", "토"];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">일정 캘린더</h1>
          <p className="text-muted-foreground">월별 일정을 확인하세요</p>
        </div>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          일정 추가
        </Button>
      </div>

      <Card className="glass-card">
        <CardHeader>
          <div className="flex items-center justify-between">
            <Button variant="ghost" size="icon" onClick={prevMonth}>
              <ChevronLeft className="h-5 w-5" />
            </Button>
            <CardTitle className="text-xl">
              {year}년 {monthNames[month]}
            </CardTitle>
            <Button variant="ghost" size="icon" onClick={nextMonth}>
              <ChevronRight className="h-5 w-5" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Day Headers */}
          <div className="grid grid-cols-7 gap-1 mb-2">
            {dayNames.map((day, index) => (
              <div
                key={day}
                className={cn(
                  "text-center py-2 text-sm font-medium",
                  index === 0 && "text-destructive",
                  index === 6 && "text-primary"
                )}
              >
                {day}
              </div>
            ))}
          </div>

          {/* Calendar Grid */}
          <div className="grid grid-cols-7 gap-1">
            {days.map((day, index) => {
              const dayEvents = day ? getEventsForDay(day) : [];
              const isToday = day === 22; // Simulating today as Jan 22

              return (
                <div
                  key={index}
                  className={cn(
                    "min-h-[100px] p-2 rounded-lg border border-border/50 transition-colors",
                    day ? "bg-card hover:bg-secondary/30 cursor-pointer" : "bg-transparent",
                    isToday && "ring-2 ring-primary"
                  )}
                >
                  {day && (
                    <>
                      <div className={cn(
                        "text-sm font-medium mb-1",
                        index % 7 === 0 && "text-destructive",
                        index % 7 === 6 && "text-primary",
                        isToday && "text-primary font-bold"
                      )}>
                        {day}
                      </div>
                      <div className="space-y-1">
                        {dayEvents.slice(0, 3).map((event) => (
                          <div
                            key={event.id}
                            className={cn(
                              "text-xs px-1.5 py-0.5 rounded truncate text-foreground",
                              typeColors[event.type as keyof typeof typeColors]
                            )}
                          >
                            {event.title}
                          </div>
                        ))}
                        {dayEvents.length > 3 && (
                          <div className="text-xs text-muted-foreground">
                            +{dayEvents.length - 3} 더보기
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Legend */}
      <div className="flex gap-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-primary" />
          <span className="text-sm text-muted-foreground">미팅</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-chart-4" />
          <span className="text-sm text-muted-foreground">화상회의</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-success" />
          <span className="text-sm text-muted-foreground">전화</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-warning" />
          <span className="text-sm text-muted-foreground">태스크</span>
        </div>
      </div>
    </div>
  );
}
