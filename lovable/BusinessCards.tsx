import { useState } from "react";
import { Plus, Search, Phone, Mail, Building2, Upload, Grid, List } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const businessCards = [
  {
    id: 1,
    name: "김철수",
    position: "구매팀장",
    company: "(주)테크솔루션",
    phone: "010-1234-5678",
    email: "kim@techsol.co.kr",
    address: "서울시 강남구 테헤란로 123",
    addedDate: "2024-01-15",
  },
  {
    id: 2,
    name: "이영희",
    position: "대표이사",
    company: "글로벌트레이딩",
    phone: "010-2345-6789",
    email: "lee@globaltr.com",
    address: "서울시 종로구 세종대로 456",
    addedDate: "2024-01-18",
  },
  {
    id: 3,
    name: "박민수",
    position: "생산부장",
    company: "스마트제조(주)",
    phone: "010-3456-7890",
    email: "park@mfg.co.kr",
    address: "경기도 수원시 영통구 광교로 789",
    addedDate: "2024-01-10",
  },
  {
    id: 4,
    name: "최지은",
    position: "기획실장",
    company: "헬스케어파트너스",
    phone: "010-4567-8901",
    email: "choi@partner.kr",
    address: "서울시 서초구 반포대로 234",
    addedDate: "2024-01-20",
  },
  {
    id: 5,
    name: "정대현",
    position: "사업개발팀장",
    company: "에코그린에너지",
    phone: "010-5678-9012",
    email: "jung@green.co.kr",
    address: "인천시 연수구 컨벤시아대로 567",
    addedDate: "2024-01-12",
  },
  {
    id: 6,
    name: "한미래",
    position: "마케팅이사",
    company: "디지털미디어(주)",
    phone: "010-6789-0123",
    email: "han@digital.co.kr",
    address: "서울시 마포구 월드컵로 890",
    addedDate: "2024-01-08",
  },
];

export default function BusinessCards() {
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  const filteredCards = businessCards.filter(
    (card) =>
      card.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      card.company.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">명함관리</h1>
          <p className="text-muted-foreground">명함을 스캔하고 관리하세요</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="gap-2">
            <Upload className="h-4 w-4" />
            명함 스캔
          </Button>
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            명함 추가
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="glass-card">
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold">{businessCards.length}</p>
            <p className="text-sm text-muted-foreground">전체 명함</p>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-primary">
              {new Set(businessCards.map((c) => c.company)).size}
            </p>
            <p className="text-sm text-muted-foreground">회사</p>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-success">3</p>
            <p className="text-sm text-muted-foreground">이번 주 추가</p>
          </CardContent>
        </Card>
      </div>

      {/* Search and View Toggle */}
      <div className="flex items-center justify-between">
        <div className="relative w-full max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="이름, 회사명 검색..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-secondary/50"
          />
        </div>
        <div className="flex gap-1">
          <Button
            variant={viewMode === "grid" ? "default" : "ghost"}
            size="icon"
            onClick={() => setViewMode("grid")}
          >
            <Grid className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === "list" ? "default" : "ghost"}
            size="icon"
            onClick={() => setViewMode("list")}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Cards Grid/List */}
      <div
        className={cn(
          viewMode === "grid"
            ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
            : "space-y-3"
        )}
      >
        {filteredCards.map((card) => (
          <Card
            key={card.id}
            className="glass-card hover:glow-border transition-all cursor-pointer"
          >
            <CardContent className={cn("p-5", viewMode === "list" && "flex items-center gap-6")}>
              <div className={cn(viewMode === "list" && "flex-1")}>
                <div className="mb-3">
                  <h3 className="text-lg font-bold text-foreground">{card.name}</h3>
                  <p className="text-sm text-muted-foreground">{card.position}</p>
                </div>
                <div className="space-y-2">
                  <p className="flex items-center gap-2 text-sm">
                    <Building2 className="h-4 w-4 text-primary" />
                    {card.company}
                  </p>
                  <p className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Phone className="h-4 w-4" />
                    {card.phone}
                  </p>
                  <p className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Mail className="h-4 w-4" />
                    {card.email}
                  </p>
                </div>
              </div>
              {viewMode === "list" && (
                <div className="flex gap-2">
                  <Button variant="outline" size="sm">
                    <Phone className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="sm">
                    <Mail className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
