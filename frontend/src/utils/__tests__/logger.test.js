import logger from '../logger';

describe('logger', () => {
  let log;
  let warn;
  let error;
  beforeEach(() => {
    log = jest.spyOn(console, 'log').mockImplementation(() => {});
    warn = jest.spyOn(console, 'warn').mockImplementation(() => {});
    error = jest.spyOn(console, 'error').mockImplementation(() => {});
  });
  afterEach(() => {
    jest.restoreAllMocks();
    localStorage.clear();
  });

  test('affiche debug et warn en développement', () => {
    logger.debug('a');
    logger.warn('b');
    expect(log).toHaveBeenCalledWith('a');
    expect(warn).toHaveBeenCalledWith('b');
  });

  test('silencieux en production sauf si le mode debug est activé', () => {
    const env = process.env.NODE_ENV;
    process.env.NODE_ENV = 'production';
    try {
      logger.debug('caché');
      logger.warn('caché');
      expect(log).not.toHaveBeenCalled();
      expect(warn).not.toHaveBeenCalled();

      localStorage.setItem('booktime_debug', '1');
      logger.debug('visible');
      expect(log).toHaveBeenCalledWith('visible');

      logger.error('toujours');
      expect(error).toHaveBeenCalledWith('toujours');
    } finally {
      process.env.NODE_ENV = env;
    }
  });

  test('error alimente l’historique et les observateurs, même défaillants', () => {
    const seen = [];
    const off = logger.onError((args) => seen.push(args[0]));
    const off2 = logger.onError(() => {
      throw new Error('observateur cassé');
    });
    logger.error('boom', new Error('détail'));
    expect(seen).toEqual(['boom']);
    expect(logger.getRecentErrors().pop().message).toContain('boom');
    off();
    off2();
    logger.error('après désinscription');
    expect(seen).toEqual(['boom']);
  });

  test('utilisable comme rappel (pas de dépendance à this)', async () => {
    await Promise.reject(new Error('x')).catch(logger.error);
    expect(error).toHaveBeenCalled();
  });
});
