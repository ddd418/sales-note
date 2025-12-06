import { useState } from "react";
import { Plus, MoreHorizontal, DollarSign, Calendar, User } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

interface Deal {
  id: number;
  title: string;
  company: string;
  value: number;
  owner: string;
  expectedClose: string;
  stage: string;
}

const initialDeals: Deal[] = [
  { id: 1, title: "ERP 도입", company: "(주)테크솔루션", value: 50000000, owner: "김영업", expectedClose: "2024-02-15", stage: "lead" },
  { id: 2, title: "CRM 시스템", company: "글로벌트레이딩", value: 35000000, owner: "이매출", expectedClose: "2024-02-20", stage: "meeting" },
  { id: 3, title: "물류 자동화", company: "스마트제조(주)", value: 80000000, owner: "박실적", expectedClose: "2024-03-01", stage: "quote" },
  { id: 4, title: "의료정보시스템", company: "헬스케어파트너스", value: 120000000, owner: "최목표", expectedClose: "2024-02-28", stage: "negotiation" },
  { id: 5, title: "에너지관리", company: "에코그린에너지", value: 95000000, owner: "김영업", expectedClose: "2024-02-10", stage: "contract" },
  { id: 6, title: "SCM 솔루션", company: "대한물류", value: 45000000, owner: "이매출", expectedClose: "2024-02-25", stage: "lead" },
  { id: 7, title: "HR시스템", company: "인재관리(주)", value: 28000000, owner: "박실적", expectedClose: "2024-03-10", stage: "meeting" },
  { id: 8, title: "회계시스템", company: "정확회계법인", value: 55000000, owner: "최목표", expectedClose: "2024-02-18", stage: "quote" },
];

const stages = [
  { id: "lead", title: "리드", color: "bg-chart-1" },
  { id: "meeting", title: "미팅", color: "bg-chart-4" },
  { id: "quote", title: "견적", color: "bg-warning" },
  { id: "negotiation", title: "협상", color: "bg-chart-2" },
  { id: "contract", title: "계약", color: "bg-success" },
];

export default function Funnel() {
  const [deals] = useState<Deal[]>(initialDeals);

  const getDealsByStage = (stageId: string) => deals.filter((d) => d.stage === stageId);

  const getStageTotal = (stageId: string) => {
    return getDealsByStage(stageId).reduce((acc, d) => acc + d.value, 0);
  };

  const formatCurrency = (value: number) => {
    if (value >= 100000000) {
      return `₩${(value / 100000000).toFixed(1)}억`;
    }
    return `₩${(value / 10000000).toFixed(0)}천만`;
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">펀넬관리</h1>
          <p className="text-muted-foreground">영업 파이프라인을 관리하세요</p>
        </div>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          딜 추가
        </Button>
      </div>

      {/* Pipeline Summary */}
      <div className="grid grid-cols-5 gap-4">
        {stages.map((stage) => (
          <Card key={stage.id} className="glass-card">
            <CardContent className="p-4 text-center">
              <div className={cn("w-3 h-3 rounded-full mx-auto mb-2", stage.color)} />
              <p className="text-sm text-muted-foreground">{stage.title}</p>
              <p className="text-xl font-bold">{getDealsByStage(stage.id).length}건</p>
              <p className="text-sm text-primary">{formatCurrency(getStageTotal(stage.id))}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Kanban Board */}
      <div className="grid grid-cols-5 gap-4 min-h-[600px]">
        {stages.map((stage) => (
          <div key={stage.id} className="flex flex-col">
            <div className="flex items-center gap-2 mb-4">
              <div className={cn("w-3 h-3 rounded-full", stage.color)} />
              <h3 className="font-semibold">{stage.title}</h3>
              <Badge variant="secondary" className="ml-auto">
                {getDealsByStage(stage.id).length}
              </Badge>
            </div>
            <div className="flex-1 space-y-3">
              {getDealsByStage(stage.id).map((deal) => (
                <Card
                  key={deal.id}
                  className="glass-card hover:glow-border transition-all cursor-grab active:cursor-grabbing"
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-sm">{deal.title}</h4>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-6 w-6">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>상세 보기</DropdownMenuItem>
                          <DropdownMenuItem>수정</DropdownMenuItem>
                          <DropdownMenuItem className="text-destructive">삭제</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                    <p className="text-xs text-muted-foreground mb-3">{deal.company}</p>
                    <div className="space-y-2 text-xs">
                      <div className="flex items-center gap-2 text-primary">
                        <DollarSign className="h-3 w-3" />
                        {formatCurrency(deal.value)}
                      </div>
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Calendar className="h-3 w-3" />
                        {deal.expectedClose}
                      </div>
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <User className="h-3 w-3" />
                        {deal.owner}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
