import { useState } from "react";
import { Plus, Search, Star, Trash2, Archive, Reply, Forward, Inbox, Send, File } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

const emails = [
  {
    id: 1,
    from: "김철수",
    email: "kim@techsol.co.kr",
    subject: "ERP 도입 관련 추가 질문드립니다",
    preview: "안녕하세요, 지난 미팅에서 논의된 내용 관련하여 몇 가지 추가로 확인하고 싶은 사항이 있어서...",
    date: "10:30",
    read: false,
    starred: true,
    hasAttachment: true,
  },
  {
    id: 2,
    from: "이영희",
    email: "lee@globaltr.com",
    subject: "Re: 견적서 검토 결과",
    preview: "견적서 검토 완료했습니다. 몇 가지 조정이 필요한 부분이 있어서 연락드립니다...",
    date: "09:15",
    read: true,
    starred: false,
    hasAttachment: false,
  },
  {
    id: 3,
    from: "박민수",
    email: "park@mfg.co.kr",
    subject: "내년 1분기 프로젝트 일정 논의",
    preview: "안녕하세요, 내년 1분기 진행 예정인 프로젝트 관련하여 사전 미팅 요청드립니다...",
    date: "어제",
    read: true,
    starred: false,
    hasAttachment: true,
  },
  {
    id: 4,
    from: "최지은",
    email: "choi@partner.kr",
    subject: "계약서 최종 검토 요청",
    preview: "법무팀 검토가 완료되어 최종 계약서를 첨부드립니다. 확인 후 서명 부탁드립니다...",
    date: "어제",
    read: false,
    starred: true,
    hasAttachment: true,
  },
  {
    id: 5,
    from: "정대현",
    email: "jung@green.co.kr",
    subject: "현장 방문 일정 확정",
    preview: "25일 오후 2시 현장 방문 일정 확정드립니다. 주차는 지하 2층에서 가능합니다...",
    date: "1월 18일",
    read: true,
    starred: false,
    hasAttachment: false,
  },
];

const folders = [
  { id: "inbox", name: "받은편지함", icon: Inbox, count: 24 },
  { id: "sent", name: "보낸편지함", icon: Send, count: 156 },
  { id: "starred", name: "중요편지함", icon: Star, count: 8 },
  { id: "archive", name: "보관함", icon: Archive, count: 45 },
  { id: "trash", name: "휴지통", icon: Trash2, count: 3 },
];

export default function Mailbox() {
  const [selectedFolder, setSelectedFolder] = useState("inbox");
  const [selectedEmail, setSelectedEmail] = useState<number | null>(null);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">메일함</h1>
          <p className="text-muted-foreground">이메일을 관리하세요</p>
        </div>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          메일 작성
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <Card className="glass-card lg:col-span-1">
          <CardContent className="p-4">
            <nav className="space-y-1">
              {folders.map((folder) => (
                <button
                  key={folder.id}
                  onClick={() => setSelectedFolder(folder.id)}
                  className={cn(
                    "w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors",
                    selectedFolder === folder.id
                      ? "bg-primary/10 text-primary"
                      : "hover:bg-secondary text-muted-foreground hover:text-foreground"
                  )}
                >
                  <div className="flex items-center gap-3">
                    <folder.icon className="h-4 w-4" />
                    <span className="text-sm font-medium">{folder.name}</span>
                  </div>
                  {folder.count > 0 && (
                    <Badge variant="secondary" className="text-xs">
                      {folder.count}
                    </Badge>
                  )}
                </button>
              ))}
            </nav>
          </CardContent>
        </Card>

        {/* Email List */}
        <Card className="glass-card lg:col-span-3">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">
                {folders.find((f) => f.id === selectedFolder)?.name}
              </CardTitle>
              <div className="relative w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input placeholder="메일 검색..." className="pl-9 bg-secondary/50" />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {emails.map((email) => (
                <div
                  key={email.id}
                  onClick={() => setSelectedEmail(email.id)}
                  className={cn(
                    "flex items-start gap-4 p-4 rounded-lg cursor-pointer transition-colors",
                    !email.read ? "bg-primary/5" : "bg-secondary/30",
                    "hover:bg-secondary/50"
                  )}
                >
                  <Avatar className="h-10 w-10">
                    <AvatarFallback className="bg-primary/10 text-primary">
                      {email.from.slice(0, 2)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className={cn("font-medium", !email.read && "text-primary")}>
                          {email.from}
                        </span>
                        {email.starred && <Star className="h-4 w-4 text-warning fill-warning" />}
                        {email.hasAttachment && <File className="h-4 w-4 text-muted-foreground" />}
                      </div>
                      <span className="text-xs text-muted-foreground">{email.date}</span>
                    </div>
                    <p className={cn("text-sm mb-1", !email.read ? "font-medium" : "text-muted-foreground")}>
                      {email.subject}
                    </p>
                    <p className="text-xs text-muted-foreground truncate">{email.preview}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
