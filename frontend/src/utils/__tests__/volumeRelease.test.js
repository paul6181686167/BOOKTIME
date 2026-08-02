import { isVolumeUnreleased, countReleasedVolumes } from '../volumeRelease';

const ironGold = {
  name: 'Iron Gold',
  volumes: 4,
  volume_details: {
    1: { pages: 624, published_year: 2018, released: true },
    2: { pages: 800, published_year: 2019, released: true },
    3: { pages: 688, published_year: 2023, released: true },
    4: { pages: null, published_year: null, released: false },
  },
};

describe('volumeRelease', () => {
  test('Red God is unreleased', () => {
    expect(isVolumeUnreleased(ironGold, 4)).toBe(true);
    expect(isVolumeUnreleased(ironGold, 3)).toBe(false);
  });

  test('countReleasedVolumes excludes Red God', () => {
    expect(countReleasedVolumes(ironGold, 4)).toBe(3);
  });
});
