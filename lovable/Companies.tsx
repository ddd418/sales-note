import { useState } from "react";
import { Plus, Search, MoreHorizontal, Building2, Phone, Mail, MapPin } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const companies = [
  {
    id: 1,
    name: "(주)테크솔루션",
    industry: "IT/소프트웨어",
    contact: "김대표",
    phone: "02-1234-5678",
    email: "contact@techsol.co.kr",
    location: "서울 강남구",
    status: "활성",
    deals: 3,
    revenue: "₩150,000,000",
  },
  {
    id: 2,
    name: "글로벌트레이딩",
    industry: "무역/유통",
    contact: "이사장",
    phone: "02-2345-6789",
    email: "info@globaltr.com",
    location: "서울 종로구",
    status: "활성",
    deals: 5,
    revenue: "₩280,000,000",
  },
  {
    id: 3,
    name: "스마트제조(주)",
    industry: "제조업",
    contact: "박부장",
    phone: "031-345-6789",
    email: "smart@mfg.co.kr",
    location: "경기 수원시",
    status: "비활성",
    deals: 1,
    revenue: "₩45,000,000",
  },
  {
    id: 4,
    name: "헬스케어파트너스",
    industry: "의료/헬스케어",
    contact: "최원장",
    phone: "02-456-7890",
    email: "health@partner.kr",
    location: "서울 서초구",
    status: "활성",
    deals: 2,
    revenue: "₩95,000,000",
  },
  {
    id: 5,
    name: "에코그린에너지",
    industry: "에너지/환경",
    contact: "정대리",
    phone: "032-567-8901",
    email: "eco@green.co.kr",
    location: "인천 연수구",
    status: "활성",
    deals: 4,
    revenue: "₩320,000,000",
  },
];

export default function Companies() {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredCompanies = companies.filter((company) =>
    company.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    company.industry.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">업체관리</h1>
          <p className="text-muted-foreground">등록된 업체를 관리하세요</p>
        </div>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          업체 추가
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="glass-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Building2 className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold">{companies.length}</p>
                <p className="text-sm text-muted-foreground">전체 업체</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-success/10">
                <Building2 className="h-5 w-5 text-success" />
              </div>
              <div>
                <p className="text-2xl font-bold">{companies.filter(c => c.status === "활성").length}</p>
                <p className="text-sm text-muted-foreground">활성 업체</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-warning/10">
                <Building2 className="h-5 w-5 text-warning" />
              </div>
              <div>
                <p className="text-2xl font-bold">{companies.reduce((acc, c) => acc + c.deals, 0)}</p>
                <p className="text-sm text-muted-foreground">진행중 딜</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-chart-4/10">
                <Building2 className="h-5 w-5 text-chart-4" />
              </div>
              <div>
                <p className="text-2xl font-bold">₩890M</p>
                <p className="text-sm text-muted-foreground">총 거래액</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Table */}
      <Card className="glass-card">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">업체 목록</CardTitle>
            <div className="relative w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="업체명, 업종 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 bg-secondary/50"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow className="border-border hover:bg-transparent">
                <TableHead>업체명</TableHead>
                <TableHead>업종</TableHead>
                <TableHead>담당자</TableHead>
                <TableHead>연락처</TableHead>
                <TableHead>위치</TableHead>
                <TableHead>상태</TableHead>
                <TableHead>진행 딜</TableHead>
                <TableHead className="text-right">총 거래액</TableHead>
                <TableHead className="w-10"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCompanies.map((company) => (
                <TableRow key={company.id} className="border-border hover:bg-secondary/30">
                  <TableCell className="font-medium">{company.name}</TableCell>
                  <TableCell className="text-muted-foreground">{company.industry}</TableCell>
                  <TableCell>{company.contact}</TableCell>
                  <TableCell>
                    <div className="flex flex-col gap-1">
                      <span className="flex items-center gap-1 text-sm">
                        <Phone className="h-3 w-3 text-muted-foreground" />
                        {company.phone}
                      </span>
                      <span className="flex items-center gap-1 text-sm text-muted-foreground">
                        <Mail className="h-3 w-3" />
                        {company.email}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="flex items-center gap-1 text-sm">
                      <MapPin className="h-3 w-3 text-muted-foreground" />
                      {company.location}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Badge variant={company.status === "활성" ? "default" : "secondary"}>
                      {company.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-center">{company.deals}</TableCell>
                  <TableCell className="text-right font-medium">{company.revenue}</TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>상세 보기</DropdownMenuItem>
                        <DropdownMenuItem>수정</DropdownMenuItem>
                        <DropdownMenuItem className="text-destructive">삭제</DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
