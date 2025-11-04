const cookies = require('cookie');
const jwt = require('jsonwebtoken');
const {
  registerUser,
  resetPassword,
  setAuthTokens,
  requestPasswordReset,
} = require('~/server/services/AuthService');
const { findSession, getUserById, deleteAllUserSessions } = require('~/models');
const { logger } = require('~/config');

const registrationController = async (req, res) => {
  try {
    const response = await registerUser(req.body);
    const { status, message } = response;
    res.status(status).send({ message });
  } catch (err) {
    logger.error('[registrationController]', err);
    return res.status(500).json({ message: err.message });
  }
};

const resetPasswordRequestController = async (req, res) => {
  try {
    const resetService = await requestPasswordReset(req);
    if (resetService instanceof Error) {
      return res.status(400).json(resetService);
    } else {
      return res.status(200).json(resetService);
    }
  } catch (e) {
    logger.error('[resetPasswordRequestController]', e);
    return res.status(400).json({ message: e.message });
  }
};

const resetPasswordController = async (req, res) => {
  try {
    const resetPasswordService = await resetPassword(
      req.body.userId,
      req.body.token,
      req.body.password,
    );
    if (resetPasswordService instanceof Error) {
      return res.status(400).json(resetPasswordService);
    } else {
      await deleteAllUserSessions({ userId: req.body.userId });
      return res.status(200).json(resetPasswordService);
    }
  } catch (e) {
    logger.error('[resetPasswordController]', e);
    return res.status(400).json({ message: e.message });
  }
};

const refreshController = async (req, res) => {
  // Auto-authenticate dev user in development mode
  if (process.env.NODE_ENV === 'development') {
    const User = require('~/models/User');
    const Balance = require('~/models/Balance');
    const { getBalanceConfig } = require('~/server/services/Config');

    let devUser = await User.findOne({ email: 'dev@librechat.local' }, '-password -__v -totpSecret');

    if (!devUser) {
      devUser = await User.create({
        email: 'dev@librechat.local',
        username: 'dev',
        name: 'Development User',
        emailVerified: true,
        role: 'ADMIN',
      });
      console.log('Created dev user for auto-authentication');
    }

    // Ensure balance exists for dev user and update config
    const balanceConfig = await getBalanceConfig();
    if (balanceConfig?.enabled && balanceConfig.startBalance != null) {
      let balance = await Balance.findOne({ user: devUser._id });

      if (!balance) {
        await Balance.create({
          user: devUser._id,
          tokenCredits: balanceConfig.startBalance,
          autoRefillEnabled: balanceConfig.autoRefillEnabled,
          refillIntervalValue: balanceConfig.refillIntervalValue,
          refillIntervalUnit: balanceConfig.refillIntervalUnit,
          refillAmount: balanceConfig.refillAmount,
        });
        console.log(`Created balance for dev user with ${balanceConfig.startBalance} tokens`);
      } else {
        // Update balance config if it changed
        const needsUpdate =
          balance.autoRefillEnabled !== balanceConfig.autoRefillEnabled ||
          balance.refillIntervalValue !== balanceConfig.refillIntervalValue ||
          balance.refillIntervalUnit !== balanceConfig.refillIntervalUnit ||
          balance.refillAmount !== balanceConfig.refillAmount;

        // Also cap balance at maxBalance if it exceeds the new limit
        const exceedsMaxBalance = balanceConfig.maxBalance != null && balance.tokenCredits > balanceConfig.maxBalance;

        if (needsUpdate || exceedsMaxBalance) {
          const updateFields = {
            autoRefillEnabled: balanceConfig.autoRefillEnabled,
            refillIntervalValue: balanceConfig.refillIntervalValue,
            refillIntervalUnit: balanceConfig.refillIntervalUnit,
            refillAmount: balanceConfig.refillAmount,
          };

          // Cap the current balance at maxBalance if needed
          if (exceedsMaxBalance) {
            updateFields.tokenCredits = balanceConfig.maxBalance;
          }

          await Balance.updateOne(
            { user: devUser._id },
            { $set: updateFields }
          );

          if (exceedsMaxBalance) {
            console.log(`Updated balance config for dev user and capped balance from ${balance.tokenCredits} to ${balanceConfig.maxBalance} tokens`);
          } else {
            console.log(`Updated balance config for dev user: refill ${balanceConfig.refillAmount} every ${balanceConfig.refillIntervalValue} ${balanceConfig.refillIntervalUnit}`);
          }
        } else {
          console.log(`Dev user balance: ${balance.tokenCredits} tokens`);
        }
      }
    }

    const token = await setAuthTokens(devUser._id, res);
    return res.status(200).send({ token, user: devUser });
  }

  const refreshToken = req.headers.cookie ? cookies.parse(req.headers.cookie).refreshToken : null;
  if (!refreshToken) {
    return res.status(200).send('Refresh token not provided');
  }

  try {
    const payload = jwt.verify(refreshToken, process.env.JWT_REFRESH_SECRET);
    const user = await getUserById(payload.id, '-password -__v -totpSecret');
    if (!user) {
      return res.status(401).redirect('/login');
    }

    const userId = payload.id;

    if (process.env.NODE_ENV === 'CI') {
      const token = await setAuthTokens(userId, res);
      return res.status(200).send({ token, user });
    }

    // Find the session with the hashed refresh token
    const session = await findSession({ userId: userId, refreshToken: refreshToken });

    if (session && session.expiration > new Date()) {
      const token = await setAuthTokens(userId, res, session._id);
      res.status(200).send({ token, user });
    } else if (req?.query?.retry) {
      // Retrying from a refresh token request that failed (401)
      res.status(403).send('No session found');
    } else if (payload.exp < Date.now() / 1000) {
      res.status(403).redirect('/login');
    } else {
      res.status(401).send('Refresh token expired or not found for this user');
    }
  } catch (err) {
    logger.error(`[refreshController] Refresh token: ${refreshToken}`, err);
    res.status(403).send('Invalid refresh token');
  }
};

module.exports = {
  refreshController,
  registrationController,
  resetPasswordController,
  resetPasswordRequestController,
};
