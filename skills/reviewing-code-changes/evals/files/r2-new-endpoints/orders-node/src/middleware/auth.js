function requireAuth(req, res, next) {
  if (!req.user) return res.status(401).json({ error: 'unauthenticated' });
  next();
}

// Loads the resource and rejects the request unless it belongs to the caller.
// Every route that takes a resource id must use this.
function requireOwner(load) {
  return async (req, res, next) => {
    const resource = await load(req);
    if (!resource) return res.status(404).json({ error: 'not found' });
    if (resource.user_id !== req.user.id) return res.status(403).json({ error: 'forbidden' });
    req.order = resource;
    next();
  };
}

module.exports = { requireAuth, requireOwner };
