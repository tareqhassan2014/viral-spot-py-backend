import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

export type QueueDocument = Queue & Document;

@Schema({ timestamps: true, collection: 'queue' })
export class Queue {
  @Prop({ type: String, required: true, index: true, maxlength: 255 })
  username: string;

  @Prop({ type: String, default: 'manual', maxlength: 100 })
  source: string;

  @Prop({
    type: String,
    enum: ['HIGH', 'LOW'],
    default: 'LOW',
    index: true,
  })
  priority: string;

  @Prop({
    type: String,
    enum: ['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'PAUSED'],
    default: 'PENDING',
    index: true,
  })
  status: string;

  @Prop({ type: Number, default: 0 })
  attempts: number;

  @Prop({ type: Date })
  last_attempt: Date;

  @Prop({ type: String })
  error_message: string;

  @Prop({ type: String, unique: true, sparse: true, maxlength: 50 })
  request_id: string;

  @Prop({ type: Date, default: Date.now })
  timestamp: Date;
}

export const QueueSchema = SchemaFactory.createForClass(Queue);
