import { Controller, Delete, Get, Param, Post } from '@nestjs/common';
import { ProfileService } from './profile.service';

@Controller('/profile')
export class ProfileController {
  constructor(private readonly profileService: ProfileService) {}

  /**
   * GET /api/profile/{username}
   * Description: Retrieves detailed data for a specific profile.
   * Usage: Used to display profile pages on the frontend.
   */
  @Get('/:username')
  getProfile(@Param('username') username: string) {
    return this.profileService.getProfile(username);
  }

  /**
   * GET /api/profile/{username}/reels
   * Description: Fetches all the reels associated with a specific profile.
   * Usage: Populates the reels section of a profile's page.
   */
  @Get('/:username/reels')
  getProfileReels(@Param('username') username: string) {
    return this.profileService.getProfileReels(username);
  }

  /**
   * GET /api/profile/{username}/similar
   * Description: Gets a list of similar profiles. This is the standard endpoint for similarity checks.
   * Usage: Suggests other profiles to the user.
   */
  @Get('/:username/similar')
  getSimilarProfiles(@Param('username') username: string) {
    return this.profileService.getSimilarProfiles(username);
  }

  /**
   * GET /api/profile/{username}/similar-fast ⚡ NEW
   * Description: A new, faster endpoint for retrieving similar profiles with 24hr caching.
   * Usage: An optimized alternative to the standard /similar endpoint with CDN-delivered images.
   */
  @Get('/:username/similar-fast')
  getSimilarProfilesFast(@Param('username') username: string) {
    return this.profileService.getSimilarProfilesFast(username);
  }

  /**
   * DELETE /api/profile/{username}/similar-cache ⚡ NEW
   * Description: Clears cached similar profiles data for a specific username with advanced cache management.
   * Usage: Cache management, data refresh, and performance optimization for similar profiles system.
   */
  @Delete('/:username/similar-cache')
  clearSimilarProfilesCache(@Param('username') username: string) {
    return this.profileService.clearSimilarProfilesCache(username);
  }

  /**
   * GET /api/profile/{username}/secondary
   * Description: Retrieves secondary (discovered) profiles associated with a primary profile.
   * Usage: Can be used to show how the network of profiles is expanding.
   */
  @Get('/:username/secondary')
  getSecondaryProfiles(@Param('username') username: string) {
    return this.profileService.getSecondaryProfiles(username);
  }

  /**
   * GET /api/profile/{username}/status
   * Description: Checks the processing status of a profile.
   * Usage: Allows the frontend to poll for updates after requesting a profile to be processed.
   */
  @Get('/:username/status')
  getProfileStatus(@Param('username') username: string) {
    return this.profileService.getProfileStatus(username);
  }

  /**
   * POST /api/profile/{username}/request
   * Description: Submits a request to scrape and analyze a new profile.
   * Usage: The primary way for users to add new profiles to the system.
   */
  @Post('/:username/request')
  requestProfileProcessing(@Param('username') username: string) {
    return this.profileService.requestProfileProcessing(username);
  }

  /**
   * POST /api/profile/{primary_username}/add-competitor/{target_username} ⚡ NEW
   * Description: Adds a target_username as a competitor to a primary_username.
   * Usage: Part of a new competitor analysis feature.
   */
  @Post('/:primary_username/add-competitor/:target_username')
  addCompetitor(
    @Param('primary_username') primaryUsername: string,
    @Param('target_username') targetUsername: string,
  ) {
    return this.profileService.addCompetitor(primaryUsername, targetUsername);
  }
}
