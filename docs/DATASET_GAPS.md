# Dataset Gaps

This note is based on the current registry cache.

## Current Non-NSFW Coverage

Total poses: `838`

Non-NSFW poses: `126`

Non-NSFW pose categories:

```text
standing: 59
sitting: 34
special: 33
```

Non-NSFW gender balance:

```text
female/f: 65
male/m: 61
```

## Missing Non-NSFW Categories

High-priority missing categories:

```text
kneeling
lying
squatting
all_fours / crawling
action
suspended / jumping / falling
```

These categories exist mostly or only in the NSFW variant today, so they are poor choices for general workflows unless more clean reference poses are added.

## Recommended Non-NSFW Additions

### Standing

Add neutral and production-friendly poses:

```text
neutral front
neutral side
neutral back
walking
running
arms_up
arms_forward
pointing
looking_down
looking_back
holding_object
phone_selfie
leaning_against_wall
```

### Sitting

The current non-NSFW sitting set is mostly thinking, crossed legs, stairs, and desk poses. Add:

```text
sitting_on_chair
sitting_side_view
sitting_back_view
sitting_relaxed
sitting_arms_crossed
sitting_hands_on_knees
sitting_legs_open
sitting_legs_together
sitting_reading
sitting_phone
```

### Kneeling

Currently missing as non-NSFW:

```text
one_knee
both_knees
kneeling_side_view
kneeling_reaching
kneeling_hands_on_floor
kneeling_prayer_or_resting
```

### Lying

Currently missing as non-NSFW:

```text
lying_on_back
lying_prone
lying_side
lying_curled
lying_reading
lying_arm_up
```

### Squatting / Crouching

Currently missing as non-NSFW:

```text
squatting_front
squatting_side
crouching
crouching_reaching
low_crouch_action
```

### Crawling / All Fours

Useful clean references:

```text
crawling
hands_and_knees
bear_crawl
child_crawling_pose
hands_on_floor_transition
```

### Action

Useful clean references:

```text
jump
landing
falling
punch
kick
dodge
dance
throwing
pulling
pushing
```

## Missing Attribute Coverage

Not yet covered or weakly covered in the non-NSFW set:

```text
arms_up / hands_up
arms_forward
hands_on_floor
torso_twist
walking
running
jumping
lying
kneeling
squatting
```

When adding new poses, add both `F` and `M` variants where possible and keep depth, bone structure, and OpenPose JSON together under the same base name.

