import { Download, TrendingUp, Users, DollarSign, Target } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const monthlyRevenue = [
  { month: "1월", 매출: 45000000, 목표: 50000000 },
  { month: "2월", 매출: 52000000, 목표: 50000000 },
  { month: "3월", 매출: 48000000, 목표: 55000000 },
  { month: "4월", 매출: 61000000, 목표: 55000000 },
  { month: "5월", 매출: 59000000, 목표: 60000000 },
  { month: "6월", 매출: 72000000, 목표: 60000000 },
];

const customersByIndustry = [
  { name: "IT/소프트웨어", value: 35, color: "hsl(217, 91%, 60%)" },
  { name: "제조업", value: 25, color: "hsl(142, 76%, 36%)" },
  { name: "유통/무역", value: 20, color: "hsl(38, 92%, 50%)" },
  { name: "의료/헬스케어", value: 12, color: "hsl(280, 65%, 60%)" },
  { name: "기타", value: 8, color: "hsl(215, 20%, 65%)" },
];

const salesPerformance = [
  { name: "김영업", deals: 12, revenue: 150000000 },
  { name: "이매출", deals: 10, revenue: 120000000 },
  { name: "박실적", deals: 8, revenue: 95000000 },
  { name: "최목표", deals: 7, revenue: 85000000 },
];

const conversionData = [
  { stage: "리드", count: 120 },
  { stage: "미팅", count: 85 },
  { stage: "견적", count: 45 },
  { stage: "협상", count: 32 },
  { stage: "계약", count: 28 },
];

export default function Reports() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">고객 리포트</h1>
          <p className="text-muted-foreground">영업 성과를 분석하세요</p>
        </div>
        <Button variant="outline" className="gap-2">
          <Download className="h-4 w-4" />
          리포트 다운로드
        </Button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="glass-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <DollarSign className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold">₩337M</p>
                <p className="text-sm text-muted-foreground">총 매출</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-success/10">
                <TrendingUp className="h-5 w-5 text-success" />
              </div>
              <div>
                <p className="text-2xl font-bold">+18.5%</p>
                <p className="text-sm text-muted-foreground">전월 대비</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-chart-4/10">
                <Users className="h-5 w-5 text-chart-4" />
              </div>
              <div>
                <p className="text-2xl font-bold">156</p>
                <p className="text-sm text-muted-foreground">활성 고객</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-warning/10">
                <Target className="h-5 w-5 text-warning" />
              </div>
              <div>
                <p className="text-2xl font-bold">23.3%</p>
                <p className="text-sm text-muted-foreground">전환율</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-lg">월별 매출 현황</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={monthlyRevenue}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(217, 33%, 22%)" />
                  <XAxis dataKey="month" stroke="hsl(215, 20%, 65%)" fontSize={12} />
                  <YAxis stroke="hsl(215, 20%, 65%)" fontSize={12} tickFormatter={(v) => `${v / 1000000}M`} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(222, 47%, 14%)",
                      border: "1px solid hsl(217, 33%, 22%)",
                      borderRadius: "8px",
                    }}
                    formatter={(value: number) => [`₩${(value / 1000000).toFixed(0)}M`, ""]}
                  />
                  <Bar dataKey="매출" fill="hsl(217, 91%, 60%)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="목표" fill="hsl(215, 20%, 65%)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-lg">업종별 고객 분포</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={customersByIndustry}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {customersByIndustry.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(222, 47%, 14%)",
                      border: "1px solid hsl(217, 33%, 22%)",
                      borderRadius: "8px",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-lg">영업 담당자별 실적</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {salesPerformance.map((person, index) => (
                <div key={person.name} className="flex items-center gap-4">
                  <div className="w-8 text-center text-lg font-bold text-muted-foreground">
                    #{index + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium">{person.name}</span>
                      <span className="text-sm text-muted-foreground">{person.deals}건</span>
                    </div>
                    <div className="h-2 bg-secondary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full"
                        style={{ width: `${(person.revenue / 150000000) * 100}%` }}
                      />
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      ₩{(person.revenue / 1000000).toFixed(0)}M
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-lg">영업 퍼널 전환율</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={conversionData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(217, 33%, 22%)" horizontal={false} />
                  <XAxis type="number" stroke="hsl(215, 20%, 65%)" fontSize={12} />
                  <YAxis dataKey="stage" type="category" stroke="hsl(215, 20%, 65%)" fontSize={12} width={50} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(222, 47%, 14%)",
                      border: "1px solid hsl(217, 33%, 22%)",
                      borderRadius: "8px",
                    }}
                  />
                  <Bar dataKey="count" fill="hsl(217, 91%, 60%)" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 p-3 rounded-lg bg-secondary/30">
              <p className="text-sm text-muted-foreground">
                리드 → 계약 전환율: <span className="text-primary font-semibold">23.3%</span>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
