import { TrendingUp, TrendingDown, Users, Building2, Calendar, DollarSign } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from "recharts";

const monthlyData = [
  { month: "1월", 매출: 4500, 목표: 5000 },
  { month: "2월", 매출: 5200, 목표: 5000 },
  { month: "3월", 매출: 4800, 목표: 5500 },
  { month: "4월", 매출: 6100, 목표: 5500 },
  { month: "5월", 매출: 5900, 목표: 6000 },
  { month: "6월", 매출: 7200, 목표: 6000 },
];

const funnelData = [
  { name: "리드", value: 120, color: "hsl(217, 91%, 60%)" },
  { name: "미팅", value: 85, color: "hsl(280, 65%, 60%)" },
  { name: "견적", value: 45, color: "hsl(38, 92%, 50%)" },
  { name: "계약", value: 28, color: "hsl(142, 76%, 36%)" },
];

const activityData = [
  { name: "미팅", count: 24 },
  { name: "전화", count: 56 },
  { name: "이메일", count: 89 },
  { name: "견적", count: 15 },
];

const stats = [
  {
    title: "이번 달 매출",
    value: "₩72,000,000",
    change: "+12.5%",
    trend: "up",
    icon: DollarSign,
  },
  {
    title: "신규 업체",
    value: "23개",
    change: "+8.2%",
    trend: "up",
    icon: Building2,
  },
  {
    title: "활성 고객",
    value: "156명",
    change: "-2.1%",
    trend: "down",
    icon: Users,
  },
  {
    title: "예정 미팅",
    value: "18건",
    change: "+5.4%",
    trend: "up",
    icon: Calendar,
  },
];

export default function Dashboard() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-foreground">대시보드</h1>
        <p className="text-muted-foreground">영업 현황을 한눈에 확인하세요</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Card key={stat.title} className="glass-card hover:glow-border transition-all duration-300">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="p-2 rounded-lg bg-primary/10">
                  <stat.icon className="h-5 w-5 text-primary" />
                </div>
                <div className={`flex items-center gap-1 text-sm ${
                  stat.trend === "up" ? "text-success" : "text-destructive"
                }`}>
                  {stat.trend === "up" ? (
                    <TrendingUp className="h-4 w-4" />
                  ) : (
                    <TrendingDown className="h-4 w-4" />
                  )}
                  {stat.change}
                </div>
              </div>
              <div className="mt-4">
                <p className="text-2xl font-bold text-foreground">{stat.value}</p>
                <p className="text-sm text-muted-foreground">{stat.title}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monthly Sales Chart */}
        <Card className="glass-card lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg font-semibold">월별 매출 추이</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={monthlyData}>
                  <defs>
                    <linearGradient id="colorSales" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(217, 91%, 60%)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(217, 91%, 60%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(217, 33%, 22%)" />
                  <XAxis dataKey="month" stroke="hsl(215, 20%, 65%)" fontSize={12} />
                  <YAxis stroke="hsl(215, 20%, 65%)" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(222, 47%, 14%)",
                      border: "1px solid hsl(217, 33%, 22%)",
                      borderRadius: "8px",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="매출"
                    stroke="hsl(217, 91%, 60%)"
                    strokeWidth={2}
                    fill="url(#colorSales)"
                  />
                  <Area
                    type="monotone"
                    dataKey="목표"
                    stroke="hsl(215, 20%, 65%)"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    fill="transparent"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Funnel Chart */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-lg font-semibold">영업 퍼널</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={funnelData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {funnelData.map((entry, index) => (
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
            <div className="grid grid-cols-2 gap-2 mt-4">
              {funnelData.map((item) => (
                <div key={item.name} className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-sm text-muted-foreground">
                    {item.name}: {item.value}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Activity Chart */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-lg font-semibold">이번 주 활동 현황</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={activityData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(217, 33%, 22%)" horizontal={false} />
                <XAxis type="number" stroke="hsl(215, 20%, 65%)" fontSize={12} />
                <YAxis dataKey="name" type="category" stroke="hsl(215, 20%, 65%)" fontSize={12} width={60} />
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
        </CardContent>
      </Card>
    </div>
  );
}
