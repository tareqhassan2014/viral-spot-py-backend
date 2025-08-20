import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

export type QueueDocument = Queue & Document;

@Schema({ timestamps: true, collection: 'queue' })
export class Queue {
  @Prop({ type: String, required: true, index: true })
  username: string;

  @Prop({ type: String, default: 'manual' })
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

  @Prop(Date)
  last_attempt: Date;

  @Prop(String)
  error_message: string;

  @Prop({ type: String, unique: true, sparse: true })
  request_id: string;
}

export const QueueSchema = SchemaFactory.createForClass(Queue);
