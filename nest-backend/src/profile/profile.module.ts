import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
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
import { ProfileStatusService } from './services/profile-status.service';

@Module({
  imports: [
    MongooseModule.forFeature([
      { name: PrimaryProfile.name, schema: PrimaryProfileSchema },
      { name: SecondaryProfile.name, schema: SecondaryProfileSchema },
      { name: SimilarProfile.name, schema: SimilarProfileSchema },
      { name: Queue.name, schema: QueueSchema },
    ]),
  ],
  controllers: [ProfileController],
  providers: [ProfileService, CompetitorService, ProfileStatusService],
  exports: [ProfileService, CompetitorService, ProfileStatusService],
})
export class ProfileModule {}
