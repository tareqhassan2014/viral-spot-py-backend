import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

export type SimilarProfileDocument = SimilarProfile & Document;

@Schema({ timestamps: true, collection: 'similar_profiles' })
export class SimilarProfile {
  @Prop({ type: String, required: true, index: true })
  primary_username: string;

  @Prop({ type: String, required: true })
  similar_username: string;

  @Prop(String)
  similar_name: string;

  @Prop(String)
  profile_image_path: string;

  @Prop(String)
  profile_image_url: string;

  @Prop({ type: Number, default: 0 })
  similarity_rank: number;

  @Prop({ type: String, index: true })
  batch_id: string;

  @Prop({ type: Boolean, default: false })
  image_downloaded: boolean;

  @Prop({ type: Boolean, default: false })
  fetch_failed: boolean;
}

export const SimilarProfileSchema =
  SchemaFactory.createForClass(SimilarProfile);

// Compound index for the main lookup query
SimilarProfileSchema.index({ primary_username: 1, similarity_rank: 1 });
