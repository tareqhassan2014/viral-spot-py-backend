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

  @Prop({ type: String, required: true, index: true, maxlength: 255 })
  competitor_username: string;

  @Prop({
    type: String,
    enum: ['suggested', 'manual', 'api'],
    default: 'suggested',
    maxlength: 50,
  })
  selection_method: string;

  @Prop({ type: Boolean, default: true, index: true })
  is_active: boolean;

  @Prop({
    type: String,
    enum: ['pending', 'processing', 'completed', 'failed'],
    default: 'pending',
    maxlength: 50,
  })
  processing_status: string;

  @Prop({ type: Date, default: Date.now })
  added_at: Date;

  @Prop({ type: Date })
  removed_at: Date;
}

export const ViralIdeasCompetitorSchema =
  SchemaFactory.createForClass(ViralIdeasCompetitor);

// Performance indexes (matching SQL schema)
ViralIdeasCompetitorSchema.index({ queue_id: 1, is_active: 1 }); // For active competitor queries
ViralIdeasCompetitorSchema.index(
  { queue_id: 1, competitor_username: 1 },
  { unique: true }, // UNIQUE(queue_id, competitor_username)
);
