#!/usr/bin/python

class Tier:

  def __init__(self, id, name, image, depends_on, tier_hooks):
    self.id = id
    self.name = name
    self.image = image
    self.depends_on = depends_on if depends_on else []
    self.tier_hooks = tier_hooks if tier_hooks else []