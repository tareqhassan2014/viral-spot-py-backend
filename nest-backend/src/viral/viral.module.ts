import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { Content, ContentSchema } from '../content/schemas/content.schema';
import {
  PrimaryProfile,
  PrimaryProfileSchema,
} from '../profile/schemas/primary-profile.schema';
import {
  SecondaryProfile,
  SecondaryProfileSchema,
} from '../profile/schemas/secondary-profile.schema';
import {
  ViralAnalysisReels,
  ViralAnalysisReelsSchema,
} from './entities/viral-analysis-reels.schema';
import {
  ViralAnalysisResults,
  ViralAnalysisResultsSchema,
} from './entities/viral-analysis-results.schema';
import {
  ViralIdeasCompetitor,
  ViralIdeasCompetitorSchema,
} from './entities/viral-ideas-competitor.schema';
import {
  ViralIdeasQueue,
  ViralIdeasQueueSchema,
} from './entities/viral-ideas-queue.schema';
import {
  ViralScripts,
  ViralScriptsSchema,
} from './entities/viral-scripts.schema';
import { ProcessPendingViralIdeasService } from './services/process-pending-viral-ideas.service';
import { QueueStatusService } from './services/queue-status.service';
import { StartViralAnalysisService } from './services/start-viral-analysis.service';
import { ViralAnalysisResultsService } from './services/viral-analysis-results.service';
import { ViralAnalysisService } from './services/viral-analysis.service';
import { ViralDiscoveryService } from './services/viral-discovery.service';
import { ViralIdeasQueueCreationService } from './services/viral-ideas-queue-creation.service';
import { ViralIdeasQueueStatusService } from './services/viral-ideas-queue-status.service';
import { ViralQueueService } from './services/viral-queue.service';
import { ViralController } from './viral.controller';

@Module({
  imports: [
    MongooseModule.forFeature([
      { name: ViralScripts.name, schema: ViralScriptsSchema },
      { name: ViralIdeasQueue.name, schema: ViralIdeasQueueSchema },
      { name: ViralAnalysisReels.name, schema: ViralAnalysisReelsSchema },
      { name: ViralIdeasCompetitor.name, schema: ViralIdeasCompetitorSchema },
      { name: ViralAnalysisResults.name, schema: ViralAnalysisResultsSchema },
      { name: Content.name, schema: ContentSchema },
      { name: PrimaryProfile.name, schema: PrimaryProfileSchema },
      { name: SecondaryProfile.name, schema: SecondaryProfileSchema },
    ]),
  ],
  controllers: [ViralController],
  providers: [
    ViralQueueService,
    ViralAnalysisService,
    ViralDiscoveryService,
    ViralIdeasQueueStatusService,
    ViralIdeasQueueCreationService,
    ProcessPendingViralIdeasService,
    StartViralAnalysisService,
    QueueStatusService,
    ViralAnalysisResultsService,
  ],
  exports: [
    ViralQueueService,
    ViralAnalysisService,
    ViralDiscoveryService,
    ViralIdeasQueueStatusService,
    ViralIdeasQueueCreationService,
    ProcessPendingViralIdeasService,
    StartViralAnalysisService,
    QueueStatusService,
    ViralAnalysisResultsService,
  ],
})
export class ViralModule {}
