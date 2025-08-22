import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import {
  PrimaryProfile,
  PrimaryProfileSchema,
} from '../profile/schemas/primary-profile.schema';
import { ContentController } from './content.controller';
import { Content, ContentSchema } from './schemas/content.schema';
import { CompetitorContentService } from './services/competitor-content.service';
import { PostsService } from './services/posts.service';
import { ReelsService } from './services/reels.service';
import { UserContentService } from './services/user-content.service';

@Module({
  imports: [
    MongooseModule.forFeature([
      { name: Content.name, schema: ContentSchema },
      { name: PrimaryProfile.name, schema: PrimaryProfileSchema },
    ]),
  ],
  controllers: [ContentController],
  providers: [
    UserContentService,
    CompetitorContentService,
    ReelsService,
    PostsService,
  ],
  exports: [
    UserContentService,
    CompetitorContentService,
    ReelsService,
    PostsService,
  ],
})
export class ContentModule {}
