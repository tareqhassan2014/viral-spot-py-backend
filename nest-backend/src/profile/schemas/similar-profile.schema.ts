import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

export type SimilarProfileDocument = SimilarProfile & Document;

@Schema({ timestamps: true, collection: 'similar_profiles' })
export class SimilarProfile {
  @Prop({ type: String, required: true, maxlength: 255, index: true })
  primary_username: string;

  @Prop({ type: String, required: true, maxlength: 255 })
  similar_username: string;

  @Prop({ type: String, maxlength: 255 })
  similar_name: string;

  @Prop({ type: String })
  profile_image_path: string;

  @Prop({ type: String })
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

// Add unique constraint to match SQL UNIQUE(primary_username, similar_username)
SimilarProfileSchema.index(
  { primary_username: 1, similar_username: 1 },
  { unique: true },
);

// Compound indexes optimized for batch operations (matching SQL schema)
SimilarProfileSchema.index({
  primary_username: 1,
  similarity_rank: 1,
  image_downloaded: 1,
}); // idx_similar_profiles_batch_lookup
SimilarProfileSchema.index({
  primary_username: 1,
  image_downloaded: 1,
  similarity_rank: 1,
}); // idx_similar_profiles_ready_display
