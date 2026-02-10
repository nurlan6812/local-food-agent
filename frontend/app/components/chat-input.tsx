'use client';

import React from "react"
import { useState, useRef, KeyboardEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ImagePlus, Send, X } from 'lucide-react';
import Image from 'next/image';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSend: (message: string, images: File[]) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    setSelectedImages((prev) => [...prev, ...files]);

    // 이미지 프리뷰 생성
    files.forEach((file) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreviews((prev) => [...prev, reader.result as string]);
      };
      reader.readAsDataURL(file);
    });

    // 파일 입력 초기화
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeImage = (index: number) => {
    setSelectedImages((prev) => prev.filter((_, i) => i !== index));
    setImagePreviews((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSend = () => {
    if ((!message.trim() && selectedImages.length === 0) || disabled) return;

    onSend(message.trim(), selectedImages);
    setMessage('');
    setSelectedImages([]);
    setImagePreviews([]);

    // 텍스트 영역 포커스
    setTimeout(() => {
      textareaRef.current?.focus();
    }, 0);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="max-w-4xl mx-auto p-4">
        {/* 이미지 프리뷰 */}
        {imagePreviews.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {imagePreviews.map((preview, index) => (
              <div
                key={index}
                className="relative w-20 h-20 rounded-lg overflow-hidden bg-muted group"
              >
                <Image
                  src={preview || "/placeholder.svg"}
                  alt={`선택된 이미지 ${index + 1}`}
                  fill
                  className="object-cover"
                  sizes="80px"
                />
                <button
                  onClick={() => removeImage(index)}
                  className="absolute top-1 right-1 bg-destructive text-destructive-foreground rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                  aria-label="이미지 제거"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* 입력 영역 */}
        <div className="flex items-end gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            onChange={handleImageSelect}
            className="hidden"
          />

          <Button
            variant="outline"
            size="icon"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            className="flex-shrink-0 h-10 w-10"
            aria-label="이미지 선택"
          >
            <ImagePlus className="h-5 w-5" />
          </Button>

          <div className="flex-1 relative">
            <Textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="메시지를 입력하세요... (Shift+Enter로 줄바꾸)"
              disabled={disabled}
              className={cn(
                'min-h-[44px] max-h-[200px] resize-none pr-12',
                'focus-visible:ring-primary'
              )}
              rows={1}
            />
          </div>

          <Button
            onClick={handleSend}
            disabled={disabled || (!message.trim() && selectedImages.length === 0)}
            size="icon"
            className="flex-shrink-0 h-10 w-10"
            aria-label="전송"
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>

        <p className="text-xs text-muted-foreground mt-2 text-center">
          음식 사진을 업로드하거나 메시지를 입력해보세요
        </p>
      </div>
    </div>
  );
}
