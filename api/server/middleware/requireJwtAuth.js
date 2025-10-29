const passport = require('passport');
const User = require('~/models/User');

// Middleware to automatically authenticate as dev user in development mode
const devAuthMiddleware = async (req, res, next) => {
  if (process.env.NODE_ENV !== 'development') {
    return next();
  }

  try {
    const Balance = require('~/models/Balance');
    const { getBalanceConfig } = require('~/server/services/Config');

    // Find or create a dev user
    let devUser = await User.findOne({ email: 'dev@librechat.local' });

    if (!devUser) {
      devUser = await User.create({
        email: 'dev@librechat.local',
        username: 'dev',
        name: 'Development User',
        emailVerified: true,
        role: 'ADMIN',
      });
      console.log('Created dev user for automatic authentication');

      // Create balance record for dev user
      const balanceConfig = await getBalanceConfig();
      if (balanceConfig?.enabled && balanceConfig.startBalance != null) {
        await Balance.create({
          user: devUser._id,
          tokenCredits: balanceConfig.startBalance,
          autoRefillEnabled: balanceConfig.autoRefillEnabled,
          refillIntervalValue: balanceConfig.refillIntervalValue,
          refillIntervalUnit: balanceConfig.refillIntervalUnit,
          refillAmount: balanceConfig.refillAmount,
        });
        console.log(`Created balance for dev user with ${balanceConfig.startBalance} tokens`);
      }
    }

    // Attach user to request
    req.user = devUser;
    next();
  } catch (error) {
    console.error('Error in dev auth middleware:', error);
    next(error);
  }
};

const requireJwtAuth = (req, res, next) => {
  // In development mode, bypass JWT auth and use dev user
  if (process.env.NODE_ENV === 'development') {
    return devAuthMiddleware(req, res, next);
  }

  // In production, use normal JWT authentication
  return passport.authenticate('jwt', { session: false })(req, res, next);
};

module.exports = requireJwtAuth;
