import { Plus, Clock, MapPin, User, Video, Phone as PhoneIcon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const schedules = [
  {
    id: 1,
    title: "테크솔루션 제품 데모",
    date: "2024-01-22",
    time: "10:00",
    duration: "1시간",
    type: "meeting",
    location: "강남 오피스",
    attendees: ["김철수", "이영희"],
    notes: "ERP 솔루션 데모 진행",
  },
  {
    id: 2,
    title: "글로벌트레이딩 화상회의",
    date: "2024-01-22",
    time: "14:00",
    duration: "30분",
    type: "video",
    location: "Zoom",
    attendees: ["박민수"],
    notes: "견적 논의",
  },
  {
    id: 3,
    title: "헬스케어파트너스 전화상담",
    date: "2024-01-23",
    time: "11:00",
    duration: "20분",
    type: "call",
    location: "",
    attendees: ["최지은"],
    notes: "계약 조건 협의",
  },
  {
    id: 4,
    title: "주간 영업회의",
    date: "2024-01-24",
    time: "09:00",
    duration: "1시간",
    type: "meeting",
    location: "회의실 A",
    attendees: ["팀원 전체"],
    notes: "주간 실적 리뷰",
  },
  {
    id: 5,
    title: "에코그린에너지 현장 방문",
    date: "2024-01-25",
    time: "13:00",
    duration: "2시간",
    type: "meeting",
    location: "인천 연수구 본사",
    attendees: ["정대현", "김부장"],
    notes: "시설 투어 및 니즈 파악",
  },
];

const typeConfig = {
  meeting: { icon: User, label: "대면 미팅", color: "bg-primary/10 text-primary" },
  video: { icon: Video, label: "화상회의", color: "bg-chart-4/10 text-chart-4" },
  call: { icon: PhoneIcon, label: "전화", color: "bg-success/10 text-success" },
};

export default function Schedules() {
  // Group schedules by date
  const groupedSchedules = schedules.reduce((acc, schedule) => {
    if (!acc[schedule.date]) {
      acc[schedule.date] = [];
    }
    acc[schedule.date].push(schedule);
    return acc;
  }, {} as Record<string, typeof schedules>);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const options: Intl.DateTimeFormatOptions = { 
      weekday: 'long', 
      month: 'long', 
      day: 'numeric' 
    };
    return date.toLocaleDateString('ko-KR', options);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">일정 목록</h1>
          <p className="text-muted-foreground">예정된 일정을 확인하세요</p>
        </div>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          일정 추가
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="glass-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <User className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {schedules.filter(s => s.type === "meeting").length}
                </p>
                <p className="text-sm text-muted-foreground">대면 미팅</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-chart-4/10">
                <Video className="h-5 w-5 text-chart-4" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {schedules.filter(s => s.type === "video").length}
                </p>
                <p className="text-sm text-muted-foreground">화상회의</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-success/10">
                <PhoneIcon className="h-5 w-5 text-success" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {schedules.filter(s => s.type === "call").length}
                </p>
                <p className="text-sm text-muted-foreground">전화 상담</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Schedule List by Date */}
      <div className="space-y-6">
        {Object.entries(groupedSchedules).map(([date, dateSchedules]) => (
          <div key={date}>
            <h2 className="text-lg font-semibold text-foreground mb-3">
              {formatDate(date)}
            </h2>
            <div className="space-y-3">
              {dateSchedules.map((schedule) => {
                const TypeIcon = typeConfig[schedule.type as keyof typeof typeConfig].icon;
                return (
                  <Card key={schedule.id} className="glass-card hover:glow-border transition-all">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-4">
                        <div className="text-center min-w-[60px]">
                          <p className="text-2xl font-bold text-primary">{schedule.time}</p>
                          <p className="text-xs text-muted-foreground">{schedule.duration}</p>
                        </div>
                        <div className="h-full w-px bg-border" />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="font-semibold text-foreground">{schedule.title}</h3>
                            <Badge className={typeConfig[schedule.type as keyof typeof typeConfig].color}>
                              <TypeIcon className="h-3 w-3 mr-1" />
                              {typeConfig[schedule.type as keyof typeof typeConfig].label}
                            </Badge>
                          </div>
                          {schedule.location && (
                            <p className="flex items-center gap-1 text-sm text-muted-foreground mb-1">
                              <MapPin className="h-3 w-3" />
                              {schedule.location}
                            </p>
                          )}
                          <p className="flex items-center gap-1 text-sm text-muted-foreground mb-2">
                            <User className="h-3 w-3" />
                            {schedule.attendees.join(", ")}
                          </p>
                          {schedule.notes && (
                            <p className="text-sm text-muted-foreground bg-secondary/30 px-3 py-2 rounded-lg">
                              {schedule.notes}
                            </p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
