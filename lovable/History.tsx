import { Search, Filter, Video, Phone, User, FileText, Mail } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const historyItems = [
  {
    id: 1,
    type: "meeting",
    title: "제품 소개 미팅",
    customer: "김철수",
    company: "(주)테크솔루션",
    date: "2024-01-15",
    time: "14:00",
    duration: "1시간 30분",
    notes: "ERP 솔루션에 대한 관심 표명. 데모 요청함. 결재권자와의 추가 미팅 필요.",
    outcome: "positive",
  },
  {
    id: 2,
    type: "call",
    title: "팔로우업 전화",
    customer: "이영희",
    company: "글로벌트레이딩",
    date: "2024-01-14",
    time: "11:00",
    duration: "20분",
    notes: "견적서 검토 중. 다음 주 내 결정 예정.",
    outcome: "neutral",
  },
  {
    id: 3,
    type: "video",
    title: "온라인 프레젠테이션",
    customer: "박민수",
    company: "스마트제조(주)",
    date: "2024-01-12",
    time: "10:00",
    duration: "45분",
    notes: "예산 문제로 올해 도입 어려움. 내년 1분기 재검토 예정.",
    outcome: "negative",
  },
  {
    id: 4,
    type: "meeting",
    title: "계약 협상 미팅",
    customer: "최지은",
    company: "헬스케어파트너스",
    date: "2024-01-10",
    time: "15:00",
    duration: "2시간",
    notes: "계약 조건 대부분 합의. 법무팀 검토 후 최종 계약 예정.",
    outcome: "positive",
  },
  {
    id: 5,
    type: "email",
    title: "제안서 발송",
    customer: "정대현",
    company: "에코그린에너지",
    date: "2024-01-08",
    time: "09:30",
    duration: "-",
    notes: "맞춤형 제안서 발송. 검토 후 미팅 일정 조율 예정.",
    outcome: "neutral",
  },
];

const typeConfig = {
  meeting: { icon: User, label: "대면 미팅", color: "bg-primary/10 text-primary" },
  video: { icon: Video, label: "화상회의", color: "bg-chart-4/10 text-chart-4" },
  call: { icon: Phone, label: "전화", color: "bg-success/10 text-success" },
  email: { icon: Mail, label: "이메일", color: "bg-warning/10 text-warning" },
};

const outcomeConfig = {
  positive: { label: "긍정적", color: "bg-success text-success-foreground" },
  neutral: { label: "보류", color: "bg-secondary text-secondary-foreground" },
  negative: { label: "부정적", color: "bg-destructive text-destructive-foreground" },
};

export default function History() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">히스토리</h1>
          <p className="text-muted-foreground">미팅 및 활동 기록을 확인하세요</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="glass-card">
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold">{historyItems.length}</p>
            <p className="text-sm text-muted-foreground">전체 활동</p>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-primary">
              {historyItems.filter(h => h.type === "meeting").length}
            </p>
            <p className="text-sm text-muted-foreground">미팅</p>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-success">
              {historyItems.filter(h => h.outcome === "positive").length}
            </p>
            <p className="text-sm text-muted-foreground">긍정적 결과</p>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-chart-4">
              {historyItems.filter(h => h.type === "video").length}
            </p>
            <p className="text-sm text-muted-foreground">화상회의</p>
          </CardContent>
        </Card>
      </div>

      {/* Search & Filter */}
      <div className="flex gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="고객명, 회사명 검색..."
            className="pl-9 bg-secondary/50"
          />
        </div>
        <Button variant="outline" className="gap-2">
          <Filter className="h-4 w-4" />
          필터
        </Button>
      </div>

      {/* History Timeline */}
      <div className="space-y-4">
        {historyItems.map((item, index) => {
          const TypeIcon = typeConfig[item.type as keyof typeof typeConfig].icon;
          return (
            <Card key={item.id} className="glass-card hover:glow-border transition-all">
              <CardContent className="p-5">
                <div className="flex gap-4">
                  {/* Timeline connector */}
                  <div className="flex flex-col items-center">
                    <div className={`p-2 rounded-lg ${typeConfig[item.type as keyof typeof typeConfig].color}`}>
                      <TypeIcon className="h-5 w-5" />
                    </div>
                    {index < historyItems.length - 1 && (
                      <div className="w-0.5 h-full bg-border mt-2" />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-foreground">{item.title}</h3>
                          <Badge className={typeConfig[item.type as keyof typeof typeConfig].color}>
                            {typeConfig[item.type as keyof typeof typeConfig].label}
                          </Badge>
                          <Badge className={outcomeConfig[item.outcome as keyof typeof outcomeConfig].color}>
                            {outcomeConfig[item.outcome as keyof typeof outcomeConfig].label}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-3 text-sm text-muted-foreground">
                          <span>{item.date}</span>
                          <span>{item.time}</span>
                          {item.duration !== "-" && <span>({item.duration})</span>}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 mb-3">
                      <Avatar className="h-8 w-8">
                        <AvatarFallback className="bg-secondary text-sm">
                          {item.customer.slice(0, 2)}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="text-sm font-medium">{item.customer}</p>
                        <p className="text-xs text-muted-foreground">{item.company}</p>
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-secondary/30">
                      <div className="flex items-start gap-2">
                        <FileText className="h-4 w-4 text-muted-foreground mt-0.5" />
                        <p className="text-sm text-muted-foreground">{item.notes}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
