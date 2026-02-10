export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  images?: string[];
  restaurant?: RestaurantInfo;
  mapUrl?: string;
  timestamp: Date;
}

export interface RestaurantInfo {
  name: string;
  cuisine: string;
  rating?: number;
  address?: string;
  phone?: string;
  description?: string;
  imageUrl?: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  map_url?: string;
  images?: string[];
}
