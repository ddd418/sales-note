import { ArrowLeft, Phone, Mail, Building2, Calendar, Edit, Trash2, Plus } from "lucide-react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";

const customerData = {
  1: {
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
    address: "서울시 강남구 테헤란로 123",
    history: [
      { date: "2024-01-15", type: "미팅", content: "제품 소개 미팅 진행, 데모 요청" },
      { date: "2024-01-10", type: "전화", content: "초기 상담, 니즈 파악" },
      { date: "2024-01-05", type: "이메일", content: "제안서 발송" },
    ],
    deals: [
      { name: "ERP 솔루션 도입", value: "₩50,000,000", stage: "견적" },
    ],
  },
};

const statusConfig = {
  hot: { label: "Hot", color: "bg-destructive text-destructive-foreground" },
  warm: { label: "Warm", color: "bg-warning text-warning-foreground" },
  cold: { label: "Cold", color: "bg-secondary text-secondary-foreground" },
};

export default function FollowupDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const customer = customerData[Number(id) as keyof typeof customerData] || customerData[1];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate("/followup")}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-foreground">고객 상세</h1>
          <p className="text-muted-foreground">고객 정보 및 활동 내역</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="gap-2">
            <Edit className="h-4 w-4" />
            수정
          </Button>
          <Button variant="destructive" size="sm" className="gap-2">
            <Trash2 className="h-4 w-4" />
            삭제
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Customer Info */}
        <Card className="glass-card lg:col-span-1">
          <CardContent className="p-6">
            <div className="flex flex-col items-center text-center">
              <Avatar className="h-20 w-20 mb-4">
                <AvatarFallback className="bg-primary text-primary-foreground text-xl">
                  {customer.name.slice(0, 2)}
                </AvatarFallback>
              </Avatar>
              <h2 className="text-xl font-bold text-foreground">{customer.name}</h2>
              <p className="text-muted-foreground">{customer.position}</p>
              <Badge className={`mt-2 ${statusConfig[customer.status as keyof typeof statusConfig].color}`}>
                {statusConfig[customer.status as keyof typeof statusConfig].label}
              </Badge>
            </div>

            <Separator className="my-6" />

            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-secondary">
                  <Building2 className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">회사</p>
                  <p className="font-medium">{customer.company}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-secondary">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">전화번호</p>
                  <p className="font-medium">{customer.phone}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-secondary">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">이메일</p>
                  <p className="font-medium">{customer.email}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-secondary">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">다음 팔로우업</p>
                  <p className="font-medium text-primary">{customer.nextFollowup}</p>
                </div>
              </div>
            </div>

            <div className="mt-6 flex gap-2">
              <Button className="flex-1 gap-2">
                <Phone className="h-4 w-4" />
                전화
              </Button>
              <Button variant="outline" className="flex-1 gap-2">
                <Mail className="h-4 w-4" />
                이메일
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Activity & Deals */}
        <div className="lg:col-span-2 space-y-6">
          {/* Deals */}
          <Card className="glass-card">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg">진행중인 딜</CardTitle>
              <Button size="sm" className="gap-2">
                <Plus className="h-4 w-4" />
                딜 추가
              </Button>
            </CardHeader>
            <CardContent>
              {customer.deals.map((deal, index) => (
                <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-secondary/30">
                  <div>
                    <p className="font-medium">{deal.name}</p>
                    <p className="text-sm text-muted-foreground">단계: {deal.stage}</p>
                  </div>
                  <p className="text-lg font-bold text-primary">{deal.value}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Activity History */}
          <Card className="glass-card">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg">활동 히스토리</CardTitle>
              <Button size="sm" variant="outline" className="gap-2">
                <Plus className="h-4 w-4" />
                활동 추가
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {customer.history.map((activity, index) => (
                  <div key={index} className="flex gap-4">
                    <div className="flex flex-col items-center">
                      <div className="w-3 h-3 rounded-full bg-primary" />
                      {index < customer.history.length - 1 && (
                        <div className="w-0.5 h-full bg-border mt-2" />
                      )}
                    </div>
                    <div className="flex-1 pb-4">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline">{activity.type}</Badge>
                        <span className="text-sm text-muted-foreground">{activity.date}</span>
                      </div>
                      <p className="text-sm">{activity.content}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Notes */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-lg">메모</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">{customer.notes || "메모가 없습니다."}</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
