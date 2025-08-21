import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { Content, ContentSchema } from '../content/schemas/content.schema';
import { ProfileController } from './profile.controller';
import {
  PrimaryProfile,
  PrimaryProfileSchema,
} from './schemas/primary-profile.schema';
import { Queue, QueueSchema } from './schemas/queue.schema';
import {
  SecondaryProfile,
  SecondaryProfileSchema,
} from './schemas/secondary-profile.schema';
import {
  SimilarProfile,
  SimilarProfileSchema,
} from './schemas/similar-profile.schema';
import { CompetitorService } from './services/competitor.service';
import { ProfileReelsService } from './services/profile-reels.service';
import { ProfileRequestService } from './services/profile-request.service';
import { ProfileRetrievalService } from './services/profile-retrieval.service';
import { ProfileStatusService } from './services/profile-status.service';
import { SecondaryProfileService } from './services/secondary-profile.service';
import { SimilarProfilesCacheService } from './services/similar-profiles-cache.service';
import { SimilarProfilesFastService } from './services/similar-profiles-fast.service';
import { SimilarProfilesService } from './services/similar-profiles.service';

@Module({
  imports: [
    MongooseModule.forFeature([
      { name: Queue.name, schema: QueueSchema },
      { name: Content.name, schema: ContentSchema },
      { name: SimilarProfile.name, schema: SimilarProfileSchema },
      { name: PrimaryProfile.name, schema: PrimaryProfileSchema },
      { name: SecondaryProfile.name, schema: SecondaryProfileSchema },
    ]),
  ],
  controllers: [ProfileController],
  providers: [
    CompetitorService,
    ProfileReelsService,
    ProfileStatusService,
    ProfileRequestService,
    SimilarProfilesService,
    ProfileRetrievalService,
    SecondaryProfileService,
    SimilarProfilesFastService,
    SimilarProfilesCacheService,
  ],
  exports: [
    CompetitorService,
    ProfileReelsService,
    ProfileStatusService,
    ProfileRequestService,
    SimilarProfilesService,
    ProfileRetrievalService,
    SecondaryProfileService,
    SimilarProfilesFastService,
    SimilarProfilesCacheService,
  ],
})
export class ProfileModule {}
