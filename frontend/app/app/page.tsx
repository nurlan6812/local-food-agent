'use client';

import { useState, useRef, useEffect } from 'react';
import { ChatMessage } from '@/components/chat-message';
import { ChatInput } from '@/components/chat-input';
import { ThemeToggle } from '@/components/theme-toggle';
import { streamChatMessage, clearSession, StreamEvent } from '@/lib/api';
import type { Message } from '@/lib/types';
import { Loader2, Sparkles, RefreshCw } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { Toaster } from '@/components/ui/toaster';
import { Button } from '@/components/ui/button';

// 도구 이름 한글 매핑
const TOOL_NAMES_KR: Record<string, string> = {
  search_food_by_image: '이미지로 음식 검색',
  search_restaurant_info: '식당 정보 검색',
  search_recipe_online: '레시피 검색',
  get_restaurant_reviews: '후기 검색',
  get_nutrition_info: '영양 정보 검색',
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [toolStatus, setToolStatus] = useState<string>('');
  const [toolHistory, setToolHistory] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, toolStatus]);

  // 환영 메시지
  useEffect(() => {
    const welcomeMessage: Message = {
      id: 'welcome',
      role: 'assistant',
      content: '안녕하세요! 한국 음식 AI입니다.\n\n음식 사진을 업로드하거나 질문을 남겨주시면 음식 정보와 맛집을 추천해드릴게요!',
      timestamp: new Date(),
    };
    setMessages([welcomeMessage]);
  }, []);

  const handleClearChat = () => {
    clearSession();
    const welcomeMessage: Message = {
      id: 'welcome-' + Date.now(),
      role: 'assistant',
      content: '새 대화가 시작되었습니다.\n\n무엇을 도와드릴까요?',
      timestamp: new Date(),
    };
    setMessages([welcomeMessage]);
  };

  const handleSend = async (message: string, images: File[]) => {
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: message,
      images: images.map((img) => URL.createObjectURL(img)),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setToolStatus('');
    setToolHistory([]);

    try {
      let aiContent = '';
      let mapUrl: string | undefined;
      let aiImages: string[] = [];

      for await (const event of streamChatMessage(message, images)) {
        switch (event.type) {
          case 'tool':
            if (event.status === 'start' && event.tool) {
              const toolName = TOOL_NAMES_KR[event.tool] || event.tool;
              setToolHistory(prev => [...prev, toolName]);
              setToolStatus(`${toolName} 중...`);
            } else if (event.status === 'done') {
              setToolStatus('');
            }
            break;

          case 'tool_progress':
            // 🔥 실시간 도구 진행 상황 표시
            if (event.status) {
              setToolStatus(event.status);
            }
            break;

          case 'text':
            if (event.content) {
              aiContent += event.content;
              setMessages((prev) => {
                const existing = prev.find((m) => m.id === 'ai-streaming');
                if (existing) {
                  return prev.map((m) =>
                    m.id === 'ai-streaming' ? { ...m, content: filterContent(aiContent) } : m
                  );
                } else {
                  return [
                    ...prev,
                    {
                      id: 'ai-streaming',
                      role: 'assistant' as const,
                      content: filterContent(aiContent),
                      timestamp: new Date(),
                    },
                  ];
                }
              });
            }
            break;

          case 'done':
            mapUrl = event.map_url;
            aiImages = event.images || [];
            setToolStatus('');
            break;

          case 'error':
            throw new Error(event.message || '오류가 발생했습니다');
        }
      }

      setMessages((prev) => {
        const filtered = prev.filter((m) => m.id !== 'ai-streaming');
        return [
          ...filtered,
          {
            id: `ai-${Date.now()}`,
            role: 'assistant' as const,
            content: filterContent(aiContent),
            mapUrl,
            images: aiImages,
            timestamp: new Date(),
          },
        ];
      });
    } catch (error) {
      console.error('[Chat] Error:', error);
      toast({
        variant: 'destructive',
        title: '오류가 발생했습니다',
        description: error instanceof Error ? error.message : '메시지 전송에 실패했습니다.',
      });

      // 스트리밍 중인 메시지 제거
      setMessages((prev) => prev.filter((m) => m.id !== 'ai-streaming'));

      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: '죄송합니다. 메시지를 처리하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setToolStatus('');
      // 응답 완료 후 1.5초 뒤에 도구 히스토리 클리어
      setTimeout(() => setToolHistory([]), 1500);
    }
  };

  return (
    <div className="flex flex-col h-[100dvh] bg-gradient-to-b from-background to-muted/20">
      {/* 헤더 */}
      <header className="sticky top-0 z-10 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 safe-top">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center">
              <Sparkles className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-foreground">한국 음식 AI</h1>
              <p className="text-xs text-muted-foreground">음식 추천 어시스턴트</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleClearChat}
              className="h-9 w-9"
              aria-label="새 대화"
            >
              <RefreshCw className="h-5 w-5" />
            </Button>
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* 메시지 영역 */}
      <main className="flex-1 overflow-y-auto overscroll-contain">
        <div className="max-w-4xl mx-auto px-2 sm:px-0">
          <div className="py-4">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {(isLoading || toolStatus || toolHistory.length > 0) && (
              <div className="flex justify-start gap-3 px-4 py-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center mt-1">
                  <Loader2 className="h-5 w-5 text-primary animate-spin" />
                </div>
                <div className="flex flex-col gap-2">
                  {toolHistory.length > 0 && (
                    <div className="bg-muted/50 text-foreground rounded-2xl rounded-bl-md px-4 py-2 shadow-sm">
                      <div className="text-xs font-medium text-muted-foreground mb-1">실행된 도구:</div>
                      <div className="flex flex-wrap gap-1">
                        {toolHistory.map((tool, idx) => (
                          <span key={idx} className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">
                            {idx + 1}. {tool}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  <div className="flex items-center gap-2 bg-muted text-foreground rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
                    <span className="text-sm">{toolStatus || 'AI가 응답을 생성하고 있습니다'}</span>
                    <div className="flex gap-1">
                      <div className="w-2 h-2 rounded-full bg-current animate-bounce [animation-delay:-0.3s]" />
                      <div className="w-2 h-2 rounded-full bg-current animate-bounce [animation-delay:-0.15s]" />
                      <div className="w-2 h-2 rounded-full bg-current animate-bounce" />
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
      </main>

      {/* 입력 영역 */}
      <ChatInput onSend={handleSend} disabled={isLoading} />

      <Toaster />
    </div>
  );
}

// 내부 추론 및 태그 필터링
function filterContent(text: string): string {
  // Plan: 내부 추론 제거
  text = text.replace(/Plan:.*?(?=\n\n|\Z)/gs, '');
  // [IMAGE:url], [MAP:url] 태그 제거 (UI에서 별도 처리)
  text = text.replace(/\[IMAGE:[^\]]+\]/g, '');
  text = text.replace(/\[MAP:[^\]]+\]/g, '');
  text = text.replace(/\[검색 결과 이미지\]\s*/g, '');
  return text.trim();
}
