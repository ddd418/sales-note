import { useState } from "react";
import { Plus, Search, FileText, Download, Eye, Trash2, Folder, File, FilePlus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

const documents = [
  {
    id: 1,
    name: "테크솔루션_견적서_v2.pdf",
    type: "견적서",
    company: "(주)테크솔루션",
    size: "2.4 MB",
    createdAt: "2024-01-20",
    status: "발송완료",
  },
  {
    id: 2,
    name: "글로벌트레이딩_제안서.pdf",
    type: "제안서",
    company: "글로벌트레이딩",
    size: "5.1 MB",
    createdAt: "2024-01-18",
    status: "작성중",
  },
  {
    id: 3,
    name: "헬스케어파트너스_계약서.pdf",
    type: "계약서",
    company: "헬스케어파트너스",
    size: "1.8 MB",
    createdAt: "2024-01-15",
    status: "서명대기",
  },
  {
    id: 4,
    name: "스마트제조_NDA.pdf",
    type: "NDA",
    company: "스마트제조(주)",
    size: "0.5 MB",
    createdAt: "2024-01-12",
    status: "완료",
  },
  {
    id: 5,
    name: "에코그린_기술명세서.pdf",
    type: "기술문서",
    company: "에코그린에너지",
    size: "8.2 MB",
    createdAt: "2024-01-10",
    status: "발송완료",
  },
];

const folders = [
  { id: 1, name: "견적서", count: 24, icon: FileText },
  { id: 2, name: "제안서", count: 18, icon: FileText },
  { id: 3, name: "계약서", count: 12, icon: FileText },
  { id: 4, name: "NDA", count: 8, icon: FileText },
  { id: 5, name: "기술문서", count: 15, icon: FileText },
];

const statusConfig = {
  "발송완료": "bg-success text-success-foreground",
  "작성중": "bg-warning text-warning-foreground",
  "서명대기": "bg-chart-4 text-chart-4-foreground",
  "완료": "bg-primary text-primary-foreground",
};

export default function Documents() {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredDocuments = documents.filter(
    (doc) =>
      doc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.company.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">서류관리</h1>
          <p className="text-muted-foreground">문서를 관리하세요</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="gap-2">
            <Folder className="h-4 w-4" />
            폴더 생성
          </Button>
          <Button className="gap-2">
            <FilePlus className="h-4 w-4" />
            문서 업로드
          </Button>
        </div>
      </div>

      {/* Folder Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {folders.map((folder) => (
          <Card 
            key={folder.id} 
            className="glass-card hover:glow-border transition-all cursor-pointer"
          >
            <CardContent className="p-4 text-center">
              <Folder className="h-10 w-10 text-primary mx-auto mb-2" />
              <p className="font-medium">{folder.name}</p>
              <p className="text-sm text-muted-foreground">{folder.count}개 파일</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Search */}
      <div className="relative w-full max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="문서명, 업체명 검색..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9 bg-secondary/50"
        />
      </div>

      {/* Documents List */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-lg">최근 문서</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {filteredDocuments.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-4 rounded-lg bg-secondary/30 hover:bg-secondary/50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <File className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">{doc.name}</p>
                    <div className="flex items-center gap-3 text-sm text-muted-foreground">
                      <span>{doc.company}</span>
                      <span>·</span>
                      <span>{doc.size}</span>
                      <span>·</span>
                      <span>{doc.createdAt}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge className={statusConfig[doc.status as keyof typeof statusConfig]}>
                    {doc.status}
                  </Badge>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
