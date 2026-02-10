'use client';

import { cn } from '@/lib/utils';
import type { Message } from '@/lib/types';
import { ImageGallery } from './image-gallery';
import { RestaurantCard } from './restaurant-card';
import { MapEmbed } from './map-embed';
import { Bot, User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={cn(
        'flex w-full gap-3 px-4 py-3',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center mt-1">
          <Bot className="h-5 w-5 text-primary" />
        </div>
      )}

      <div
        className={cn(
          'flex flex-col gap-3 max-w-[85%] md:max-w-[70%]',
          isUser && 'items-end'
        )}
      >
        {/* 메시지 버블 */}
        {message.content && (
          <div
            className={cn(
              'rounded-2xl px-4 py-3 shadow-sm',
              isUser
                ? 'bg-primary text-primary-foreground rounded-br-md'
                : 'bg-muted text-foreground rounded-bl-md'
            )}
          >
            {isUser ? (
              <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                {message.content}
              </p>
            ) : (
              <div className="text-sm chat-markdown">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    a: ({ href, children }) => (
                      <a href={href} target="_blank" rel="noopener noreferrer" className="text-primary underline hover:text-primary/80">
                        {children}
                      </a>
                    ),
                    table: ({ children }) => (
                      <div className="table-wrapper">
                        <table>{children}</table>
                      </div>
                    ),
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
          </div>
        )}

        {/* 이미지 갤러리 */}
        {message.images && message.images.length > 0 && (
          <div className="w-full max-w-md">
            <ImageGallery images={message.images} />
          </div>
        )}

        {/* 식당 카드 */}
        {message.restaurant && (
          <div className="w-full max-w-md">
            <RestaurantCard restaurant={message.restaurant} />
          </div>
        )}

        {/* 지도 */}
        {message.mapUrl && (
          <div className="w-full max-w-md">
            <MapEmbed url={message.mapUrl} />
          </div>
        )}

        {/* 타임스탬프 */}
        <span className="text-xs text-muted-foreground px-2">
          {message.timestamp.toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center mt-1">
          <User className="h-5 w-5 text-primary-foreground" />
        </div>
      )}
    </div>
  );
}
