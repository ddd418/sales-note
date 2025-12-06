import { useState } from "react";
import { Bot, Building2, FileText, TrendingUp, Users, Sparkles, Search, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";

const recentPreps = [
  {
    id: 1,
    company: "(주)테크솔루션",
    date: "2024-01-22",
    status: "완료",
    insights: 5,
  },
  {
    id: 2,
    company: "글로벌트레이딩",
    date: "2024-01-20",
    status: "완료",
    insights: 8,
  },
  {
    id: 3,
    company: "에코그린에너지",
    date: "2024-01-18",
    status: "진행중",
    insights: 3,
  },
];

export default function AIMeeting() {
  const [selectedCompany, setSelectedCompany] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleAnalyze = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">AI 미팅준비</h1>
          <p className="text-muted-foreground">AI가 미팅을 준비해드립니다</p>
        </div>
      </div>

      {/* AI Input Section */}
      <Card className="glass-card glow-border">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Bot className="h-5 w-5 text-primary" />
            미팅 준비 시작
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="업체명을 입력하세요..."
              value={selectedCompany}
              onChange={(e) => setSelectedCompany(e.target.value)}
              className="pl-9 bg-secondary/50"
            />
          </div>
          <Textarea
            placeholder="미팅 목적이나 추가 정보를 입력해주세요... (선택사항)"
            className="bg-secondary/50 min-h-[100px]"
          />
          <Button 
            className="w-full gap-2" 
            onClick={handleAnalyze}
            disabled={!selectedCompany || isAnalyzing}
          >
            {isAnalyzing ? (
              <>
                <div className="h-4 w-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                분석 중...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                AI 분석 시작
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="glass-card hover:glow-border transition-all cursor-pointer">
          <CardContent className="p-4">
            <div className="p-3 rounded-lg bg-primary/10 w-fit mb-3">
              <Building2 className="h-6 w-6 text-primary" />
            </div>
            <h3 className="font-semibold mb-1">기업 정보 분석</h3>
            <p className="text-sm text-muted-foreground">
              기업 개요, 재무 현황, 최근 뉴스를 종합 분석합니다.
            </p>
          </CardContent>
        </Card>
        <Card className="glass-card hover:glow-border transition-all cursor-pointer">
          <CardContent className="p-4">
            <div className="p-3 rounded-lg bg-success/10 w-fit mb-3">
              <Users className="h-6 w-6 text-success" />
            </div>
            <h3 className="font-semibold mb-1">담당자 인사이트</h3>
            <p className="text-sm text-muted-foreground">
              미팅 담당자의 프로필과 관심사를 파악합니다.
            </p>
          </CardContent>
        </Card>
        <Card className="glass-card hover:glow-border transition-all cursor-pointer">
          <CardContent className="p-4">
            <div className="p-3 rounded-lg bg-warning/10 w-fit mb-3">
              <TrendingUp className="h-6 w-6 text-warning" />
            </div>
            <h3 className="font-semibold mb-1">시장 트렌드</h3>
            <p className="text-sm text-muted-foreground">
              해당 산업의 최신 트렌드와 기회를 분석합니다.
            </p>
          </CardContent>
        </Card>
        <Card className="glass-card hover:glow-border transition-all cursor-pointer">
          <CardContent className="p-4">
            <div className="p-3 rounded-lg bg-chart-4/10 w-fit mb-3">
              <FileText className="h-6 w-6 text-chart-4" />
            </div>
            <h3 className="font-semibold mb-1">미팅 스크립트</h3>
            <p className="text-sm text-muted-foreground">
              상황에 맞는 미팅 시나리오를 제안합니다.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Preps */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-lg">최근 미팅 준비</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recentPreps.map((prep) => (
              <div
                key={prep.id}
                className="flex items-center justify-between p-4 rounded-lg bg-secondary/30 hover:bg-secondary/50 transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-4">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <Building2 className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">{prep.company}</p>
                    <p className="text-sm text-muted-foreground">{prep.date}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <Badge variant={prep.status === "완료" ? "default" : "secondary"}>
                    {prep.status}
                  </Badge>
                  <div className="text-right">
                    <p className="text-sm text-primary font-medium">{prep.insights}개</p>
                    <p className="text-xs text-muted-foreground">인사이트</p>
                  </div>
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
