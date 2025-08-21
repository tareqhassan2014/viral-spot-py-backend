import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { Content, ContentSchema } from '../content/schemas/content.schema';
import { ProfileController } from './profile.controller';
import { ProfileService } from './profile.service';
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
      { name: PrimaryProfile.name, schema: PrimaryProfileSchema },
      { name: SecondaryProfile.name, schema: SecondaryProfileSchema },
      { name: SimilarProfile.name, schema: SimilarProfileSchema },
      { name: Queue.name, schema: QueueSchema },
      { name: Content.name, schema: ContentSchema },
    ]),
  ],
  controllers: [ProfileController],
  providers: [
    ProfileService,
    CompetitorService,
    ProfileRetrievalService,
    ProfileReelsService,
    SimilarProfilesService,
    SimilarProfilesFastService,
    ProfileStatusService,
    SimilarProfilesCacheService,
    SecondaryProfileService,
    ProfileRequestService,
  ],
  exports: [
    ProfileService,
    CompetitorService,
    ProfileRetrievalService,
    ProfileReelsService,
    SimilarProfilesService,
    SimilarProfilesFastService,
    ProfileStatusService,
    SimilarProfilesCacheService,
    SecondaryProfileService,
    ProfileRequestService,
  ],
})
export class ProfileModule {}
