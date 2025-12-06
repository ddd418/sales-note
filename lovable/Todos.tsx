import { useState } from "react";
import { Plus, Check, Circle, Calendar, Flag, Trash2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface Todo {
  id: number;
  title: string;
  completed: boolean;
  priority: "high" | "medium" | "low";
  dueDate: string;
  category: string;
}

const initialTodos: Todo[] = [
  { id: 1, title: "테크솔루션 견적서 발송", completed: false, priority: "high", dueDate: "2024-01-22", category: "영업" },
  { id: 2, title: "글로벌트레이딩 미팅 준비", completed: false, priority: "high", dueDate: "2024-01-23", category: "미팅" },
  { id: 3, title: "월간 보고서 작성", completed: true, priority: "medium", dueDate: "2024-01-25", category: "보고" },
  { id: 4, title: "신규 리드 연락", completed: false, priority: "medium", dueDate: "2024-01-24", category: "영업" },
  { id: 5, title: "제품 카탈로그 업데이트", completed: false, priority: "low", dueDate: "2024-01-30", category: "기타" },
  { id: 6, title: "CRM 데이터 정리", completed: true, priority: "low", dueDate: "2024-01-20", category: "기타" },
];

const priorityConfig = {
  high: { label: "긴급", color: "text-destructive", bg: "bg-destructive/10" },
  medium: { label: "보통", color: "text-warning", bg: "bg-warning/10" },
  low: { label: "낮음", color: "text-muted-foreground", bg: "bg-secondary" },
};

export default function Todos() {
  const [todos, setTodos] = useState<Todo[]>(initialTodos);
  const [newTodo, setNewTodo] = useState("");
  const [filter, setFilter] = useState<"all" | "active" | "completed">("all");

  const toggleTodo = (id: number) => {
    setTodos(todos.map(todo =>
      todo.id === id ? { ...todo, completed: !todo.completed } : todo
    ));
  };

  const deleteTodo = (id: number) => {
    setTodos(todos.filter(todo => todo.id !== id));
  };

  const addTodo = () => {
    if (!newTodo.trim()) return;
    const todo: Todo = {
      id: Date.now(),
      title: newTodo,
      completed: false,
      priority: "medium",
      dueDate: new Date().toISOString().split("T")[0],
      category: "기타",
    };
    setTodos([todo, ...todos]);
    setNewTodo("");
  };

  const filteredTodos = todos.filter(todo => {
    if (filter === "active") return !todo.completed;
    if (filter === "completed") return todo.completed;
    return true;
  });

  const stats = {
    total: todos.length,
    completed: todos.filter(t => t.completed).length,
    pending: todos.filter(t => !t.completed).length,
    high: todos.filter(t => t.priority === "high" && !t.completed).length,
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-foreground">TODOLIST</h1>
        <p className="text-muted-foreground">할 일을 관리하세요</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="glass-card">
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold">{stats.total}</p>
            <p className="text-sm text-muted-foreground">전체</p>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-success">{stats.completed}</p>
            <p className="text-sm text-muted-foreground">완료</p>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-warning">{stats.pending}</p>
            <p className="text-sm text-muted-foreground">진행중</p>
          </CardContent>
        </Card>
        <Card className="glass-card">
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-destructive">{stats.high}</p>
            <p className="text-sm text-muted-foreground">긴급</p>
          </CardContent>
        </Card>
      </div>

      {/* Add Todo */}
      <Card className="glass-card">
        <CardContent className="p-4">
          <div className="flex gap-2">
            <Input
              placeholder="새로운 할 일을 입력하세요..."
              value={newTodo}
              onChange={(e) => setNewTodo(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && addTodo()}
              className="bg-secondary/50"
            />
            <Button onClick={addTodo} className="gap-2">
              <Plus className="h-4 w-4" />
              추가
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <div className="flex gap-2">
        <Button
          variant={filter === "all" ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter("all")}
        >
          전체
        </Button>
        <Button
          variant={filter === "active" ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter("active")}
        >
          진행중
        </Button>
        <Button
          variant={filter === "completed" ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter("completed")}
        >
          완료
        </Button>
      </div>

      {/* Todo List */}
      <div className="space-y-2">
        {filteredTodos.map((todo) => (
          <Card
            key={todo.id}
            className={cn(
              "glass-card transition-all hover:glow-border",
              todo.completed && "opacity-60"
            )}
          >
            <CardContent className="p-4">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => toggleTodo(todo.id)}
                  className={cn(
                    "w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors",
                    todo.completed
                      ? "bg-success border-success text-success-foreground"
                      : "border-muted-foreground hover:border-primary"
                  )}
                >
                  {todo.completed && <Check className="h-4 w-4" />}
                </button>

                <div className="flex-1 min-w-0">
                  <p className={cn(
                    "font-medium truncate",
                    todo.completed && "line-through text-muted-foreground"
                  )}>
                    {todo.title}
                  </p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Calendar className="h-3 w-3" />
                      {todo.dueDate}
                    </span>
                    <Badge variant="outline" className="text-xs">
                      {todo.category}
                    </Badge>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <div className={cn(
                    "flex items-center gap-1 px-2 py-1 rounded text-xs",
                    priorityConfig[todo.priority].bg,
                    priorityConfig[todo.priority].color
                  )}>
                    <Flag className="h-3 w-3" />
                    {priorityConfig[todo.priority].label}
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-destructive"
                    onClick={() => deleteTodo(todo.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
