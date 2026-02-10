'use client';

import Image from 'next/image';
import { MapPin, Phone, Star, Utensils } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import type { RestaurantInfo } from '@/lib/types';

interface RestaurantCardProps {
  restaurant: RestaurantInfo;
}

export function RestaurantCard({ restaurant }: RestaurantCardProps) {
  return (
    <Card className="overflow-hidden border-primary/20">
      <CardContent className="p-0">
        {restaurant.imageUrl && (
          <div className="relative w-full h-48 bg-muted">
            <Image
              src={restaurant.imageUrl || "/placeholder.svg"}
              alt={restaurant.name}
              fill
              className="object-cover"
              sizes="(max-width: 768px) 100vw, 400px"
            />
          </div>
        )}
        <div className="p-4 space-y-3">
          <div>
            <h3 className="font-bold text-lg text-foreground text-balance">
              {restaurant.name}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <Utensils className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">{restaurant.cuisine}</span>
            </div>
          </div>

          {restaurant.rating && (
            <div className="flex items-center gap-1">
              <Star className="h-4 w-4 fill-primary text-primary" />
              <span className="font-medium text-foreground">{restaurant.rating.toFixed(1)}</span>
            </div>
          )}

          {restaurant.description && (
            <p className="text-sm text-muted-foreground leading-relaxed">
              {restaurant.description}
            </p>
          )}

          <div className="space-y-2 pt-2 border-t border-border">
            {restaurant.address && (
              <div className="flex items-start gap-2">
                <MapPin className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                <span className="text-sm text-foreground">{restaurant.address}</span>
              </div>
            )}
            {restaurant.phone && (
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                <span className="text-sm text-foreground">{restaurant.phone}</span>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
