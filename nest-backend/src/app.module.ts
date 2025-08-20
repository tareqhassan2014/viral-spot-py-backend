import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { ProfileModule } from './profile/profile.module';
import { ViralModule } from './viral/viral.module';

@Module({
  imports: [
    MongooseModule.forRoot('mongodb://localhost:27017/viralspot', {
      // Add connection options if needed
    }),
    ProfileModule,
    ViralModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
