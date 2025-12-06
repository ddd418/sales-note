import { useState } from "react";
import { Plus, Search, Phone, Mail, Calendar, ChevronRight, User } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useNavigate } from "react-router-dom";

const customers = [
  {
    id: 1,
    name: "김철수",
    company: "(주)테크솔루션",
    position: "구매팀장",
    phone: "010-1234-5678",
    email: "kim@techsol.co.kr",
    lastContact: "2024-01-15",
    nextFollowup: "2024-01-22",
    status: "hot",
    notes: "제품 데모 요청함",
  },
  {
    id: 2,
    name: "이영희",
    company: "글로벌트레이딩",
    position: "대표이사",
    phone: "010-2345-6789",
    email: "lee@globaltr.com",
    lastContact: "2024-01-18",
    nextFollowup: "2024-01-25",
    status: "warm",
    notes: "견적서 검토 중",
  },
  {
    id: 3,
    name: "박민수",
    company: "스마트제조(주)",
    position: "생산부장",
    phone: "010-3456-7890",
    email: "park@mfg.co.kr",
    lastContact: "2024-01-10",
    nextFollowup: "2024-01-20",
    status: "cold",
    notes: "예산 확보 대기",
  },
  {
    id: 4,
    name: "최지은",
    company: "헬스케어파트너스",
    position: "기획실장",
    phone: "010-4567-8901",
    email: "choi@partner.kr",
    lastContact: "2024-01-20",
    nextFollowup: "2024-01-27",
    status: "hot",
    notes: "계약서 검토 중",
  },
  {
    id: 5,
    name: "정대현",
    company: "에코그린에너지",
    position: "사업개발팀장",
    phone: "010-5678-9012",
    email: "jung@green.co.kr",
    lastContact: "2024-01-12",
    nextFollowup: "2024-01-19",
    status: "warm",
    notes: "2차 미팅 예정",
  },
];

const statusConfig = {
  hot: { label: "Hot", color: "bg-destructive text-destructive-foreground" },
  warm: { label: "Warm", color: "bg-warning text-warning-foreground" },
  cold: { label: "Cold", color: "bg-secondary text-secondary-foreground" },
};

export default function Followup() {
  const [searchQuery, setSearchQuery] = useState("");
  const navigate = useNavigate();

  const filteredCustomers = customers.filter((customer) =>
    customer.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    customer.company.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleCustomerClick = (customerId: number) => {
    navigate(`/followup/${customerId}`);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">팔로우업</h1>
          <p className="text-muted-foreground">고객 팔로우업을 관리하세요</p>
        </div>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          고객 추가
        </Button>
      </div>

      {/* Filter Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="glass-card cursor-pointer hover:glow-border transition-all">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold">{customers.length}</p>
                <p className="text-sm text-muted-foreground">전체 고객</p>
              </div>
              <User className="h-8 w-8 text-primary/50" />
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card cursor-pointer hover:glow-border transition-all">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold text-destructive">
                  {customers.filter(c => c.status === "hot").length}
                </p>
                <p className="text-sm text-muted-foreground">Hot 고객</p>
              </div>
              <div className="h-8 w-8 rounded-full bg-destructive/20 flex items-center justify-center">
                🔥
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card cursor-pointer hover:glow-border transition-all">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold text-warning">
                  {customers.filter(c => c.status === "warm").length}
                </p>
                <p className="text-sm text-muted-foreground">Warm 고객</p>
              </div>
              <div className="h-8 w-8 rounded-full bg-warning/20 flex items-center justify-center">
                ☀️
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card cursor-pointer hover:glow-border transition-all">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold">
                  {customers.filter(c => c.status === "cold").length}
                </p>
                <p className="text-sm text-muted-foreground">Cold 고객</p>
              </div>
              <div className="h-8 w-8 rounded-full bg-secondary flex items-center justify-center">
                ❄️
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="relative w-full max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="고객명, 회사명 검색..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9 bg-secondary/50"
        />
      </div>

      {/* Customer List */}
      <div className="grid gap-4">
        {filteredCustomers.map((customer) => (
          <Card 
            key={customer.id} 
            className="glass-card hover:glow-border transition-all cursor-pointer"
            onClick={() => handleCustomerClick(customer.id)}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <Avatar className="h-12 w-12">
                    <AvatarFallback className="bg-primary/10 text-primary">
                      {customer.name.slice(0, 2)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-foreground">{customer.name}</h3>
                      <Badge className={statusConfig[customer.status as keyof typeof statusConfig].color}>
                        {statusConfig[customer.status as keyof typeof statusConfig].label}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {customer.company} · {customer.position}
                    </p>
                    <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Phone className="h-3 w-3" />
                        {customer.phone}
                      </span>
                      <span className="flex items-center gap-1">
                        <Mail className="h-3 w-3" />
                        {customer.email}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">다음 팔로우업</p>
                    <p className="flex items-center gap-1 text-sm font-medium text-primary">
                      <Calendar className="h-3 w-3" />
                      {customer.nextFollowup}
                    </p>
                  </div>
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                </div>
              </div>
              {customer.notes && (
                <div className="mt-3 p-2 rounded-lg bg-secondary/30 text-sm text-muted-foreground">
                  💬 {customer.notes}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
