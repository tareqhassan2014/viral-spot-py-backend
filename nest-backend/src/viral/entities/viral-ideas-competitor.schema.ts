import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Schema as MongooseSchema } from 'mongoose';

export type ViralIdeasCompetitorDocument = ViralIdeasCompetitor & Document;

@Schema({ timestamps: true, collection: 'viral_ideas_competitors' })
export class ViralIdeasCompetitor {
  @Prop({
    type: MongooseSchema.Types.ObjectId,
    ref: 'ViralIdeasQueue',
    required: true,
    index: true,
  })
  queue_id: MongooseSchema.Types.ObjectId;

  @Prop({ type: String, required: true, index: true })
  competitor_username: string;

  @Prop({
    type: String,
    enum: ['suggested', 'manual', 'api'],
    default: 'suggested',
  })
  selection_method: string;

  @Prop({ type: Boolean, default: true, index: true })
  is_active: boolean;

  @Prop({
    type: String,
    enum: ['pending', 'processing', 'completed', 'failed'],
    default: 'pending',
    index: true,
  })
  processing_status: string;

  @Prop({ type: Date, default: Date.now })
  added_at: Date;

  @Prop(Date)
  removed_at: Date;

  @Prop(Date)
  processed_at: Date;

  @Prop(String)
  error_message: string;
}

export const ViralIdeasCompetitorSchema =
  SchemaFactory.createForClass(ViralIdeasCompetitor);

// Performance indexes
ViralIdeasCompetitorSchema.index({ queue_id: 1, is_active: 1 });
ViralIdeasCompetitorSchema.index({ competitor_username: 1 });
ViralIdeasCompetitorSchema.index(
  { queue_id: 1, competitor_username: 1 },
  { unique: true },
);
