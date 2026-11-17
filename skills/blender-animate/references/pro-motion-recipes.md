# Pro Motion Recipes: Overlapping Waves, Easing & Secondary Motion

Contents: 1 principles | 2 overlapping wave chains | 3 floating & crystal idles | 4 combat anticipation & overshoot | 5 visual frame verification

## 1. Core principles ("Animate Goodly")
Never keyframe all bones on the same frame with linear interpolation. Every pro animation clip uses:
1. **Phase-Offset Overlapping Wave:** Child bones lag behind parent bones by $\Delta \phi = 0.45\text{ to }0.75\text{ rad}$ per segment.
2. **Root-to-Tip Amplitude Progression:** Amplitude increases progressively from spine/neck root ($0.35 \times A$) to tail/tentacle/cape tip ($1.35 \times A$).
3. **Eased F-Curves:** Use `BEZIER` keyframes with `AUTO_CLAMPED` handles; use overshoot and settle on one-shot attacks.
4. **Constant-Volume Squash & Stretch:** Keep $S_x \cdot S_y \cdot S_z \approx 1.0$ during impacts and jumps.

## 2. Overlapping wave chains (`anim_pro_motion(motion_type="overlapping_wave")`)
- Ideal for serpentine creatures (snakes, sandworms, dragons, fish, tails, capes, tentacles).
- At frame $f \in [f_{\text{start}}, f_{\text{end}}]$ with normalized cycle phase $\theta = 2\pi \frac{f - f_{\text{start}}}{f_{\text{end}} - f_{\text{start}}}$:
  - $\text{rot}_z(b_i) = A_i \sin(\theta - i \cdot \Delta\phi)$
  - $\text{rot}_x(b_i) = 0.45 A_i \cos(\theta - i \cdot \Delta\phi)$
- Guarantees exact mathematical loop closure at $f_{\text{start}}$ and $f_{\text{end}}$ (`loop_closed = True`).

## 3. Floating & crystal idles (`anim_pro_motion(motion_type="floating_idle")`)
- Root bone bobs vertically on $Z$ ($\Delta z = 0.06 \sin\theta$) with a $90^\circ$-lagged pitch tilt ($\text{rot}_x$) while floating shards/halos orbit or bob with staggered phases $\phi_k = \frac{2\pi k}{N}$.

## 4. Combat anticipation & overshoot
- **Anticipation (15–20% of clip):** Wind up in the opposite direction of the strike ($-0.35 \times \text{strike angle}$).
- **Strike (10–15% of clip):** Fast snap through the contact pose to `+8%` overshoot.
- **Recovery / Settle (65–75% of clip):** Ease back to rest pose with a damped secondary oscillation.

## 5. Visual frame verification
Always call `look(mode="frames", target=[armature], frame_count=6, shading="material")` after keying an action to inspect the motion arc and confirm zero mesh tearing before running `audit_anim.py`.
