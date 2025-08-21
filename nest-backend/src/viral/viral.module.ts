import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
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
import { ViralAnalysisService } from './services/viral-analysis.service';
import { ViralDiscoveryService } from './services/viral-discovery.service';
import { ViralQueueService } from './services/viral-queue.service';
import { ViralController } from './viral.controller';

@Module({
  imports: [
    MongooseModule.forFeature([
      { name: ViralIdeasQueue.name, schema: ViralIdeasQueueSchema },
      { name: ViralIdeasCompetitor.name, schema: ViralIdeasCompetitorSchema },
      { name: ViralAnalysisResults.name, schema: ViralAnalysisResultsSchema },
      { name: ViralAnalysisReels.name, schema: ViralAnalysisReelsSchema },
      { name: ViralScripts.name, schema: ViralScriptsSchema },
    ]),
  ],
  controllers: [ViralController],
  providers: [ViralDiscoveryService, ViralQueueService, ViralAnalysisService],
  exports: [ViralDiscoveryService, ViralQueueService, ViralAnalysisService],
})
export class ViralModule {}
