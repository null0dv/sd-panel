# -*- coding: utf-8 -*-
"""Expand insertion poses + cute-sexy faces; reduce ahegao dominance."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANKS = ROOT / "data" / "char-banks.json"


def uniq_extend(arr, items):
    seen = set(arr)
    n = 0
    for x in items:
        if x not in seen:
            arr.append(x)
            seen.add(x)
            n += 1
    return n


def soft_ahegao(text: str) -> str:
    """Rewrite extreme ahegao toward cute-sexy arousal."""
    t = text
    reps = [
        (r"extreme ahegao[^,]*,?\s*", "flushed aroused expression, "),
        (r"intense ahegao[^,]*,?\s*", "teary bedroom eyes, parted lips, "),
        (r"kawaii ahegao blend[^,]*,?\s*", "cute overwhelmed blush, glossy parted lips, "),
        (r"innocent ahegao-lite[^,]*,?\s*", "dazed cute blush, soft open mouth, "),
        (r"ahegao-lite[^,]*,?\s*", "half-lidded lustful gaze, "),
        (r"ahegao expression", "flushed sensual expression"),
        (r"ahegao face", "aroused cute face"),
        (r"fucked silly face", "dazed pleasure blush"),
        (r",?\s*ahegao\b", ""),
    ]
    for pat, rep in reps:
        t = re.sub(pat, rep, t, flags=re.I)
    t = re.sub(r",\s*,+", ", ", t).strip(" ,")
    return t


def main():
    cb = json.loads(BANKS.read_text(encoding="utf-8"))

    # Soften existing ahegao-heavy face/pose lines
    for key in ("face", "pose", "job", "details"):
        cb[key] = [soft_ahegao(x) for x in cb[key]]

    poses = [
        # ── missionary family (cute-sexy, face contact) ──
        "missionary on bed, lying on back, legs loosely wrapped around partner, face to face, soft blush, looking at viewer, vaginal penetration, 1boy",
        "missionary, knees bent outward, holding sheets, cute teary eyes, parted lips, gentle hip motion, intimate close-up, 1boy",
        "missionary, one leg over partner shoulder, deep but soft angle, flushed cheeks, eye contact, sensual insertion, 1boy",
        "missionary pillow under hips, arched petite back, legs open, holding partner wrists, shy aroused smile, 1boy",
        "missionary edge of bed, hips at mattress edge, legs dangling then lifted, looking up seductively, 1boy",
        "missionary, interlocking fingers, forehead almost touching, slow deep thrusts, loving lewd atmosphere, 1boy",
        "missionary, legs in V shape raised, hands covering mouth shyly, blushing through fingers, penetration visible, 1boy",
        "missionary side-angle, body half turned, one knee raised, soft breast bounce, cute moan expression, 1boy",
        "folded missionary, knees toward chest, compact petite pose, looking between legs then at partner, 1boy",
        "missionary with ankle hold, legs spread by partner hands, vulnerable cute pose, glossy eyes, 1boy",
        # ── cowgirl / reverse ──
        "cowgirl, sitting upright on partner, hands on his chest, slow hip roll, cute dominant blush, looking down, 1boy",
        "cowgirl lean-forward, hands on bed, chest near face, eye contact, soft riding rhythm, 1boy",
        "cowgirl, knees wide, petite body bouncing lightly, holding own thighs, shy proud expression, 1boy",
        "reverse cowgirl, facing away, looking back over shoulder, arched back, hip grind, sensual rear view, 1boy",
        "reverse cowgirl lean back, hands behind on partner thighs, belly and hips on display, soft moan face, 1boy",
        "squatting cowgirl, feet planted, lowering onto penis, careful cute concentration, 1boy",
        "kneeling cowgirl, shins on bed, full body contact, hugging while riding, intimate cuddle sex, 1boy",
        "cowgirl pause deep, fully seated, grinding circles, biting lip, teasing stillness, 1boy",
        "lotus cowgirl, legs wrapped around partner torso face to face, rocking, soft kisses, 1boy",
        # ── doggy / prone / from behind ──
        "doggy style, on all fours, back gently arched, looking back with shy smile, rear entry, 1boy",
        "doggy, chest low on sheets, ass raised, gripping pillow, peeking back, cute lewd, 1boy",
        "doggy standing bend-over, hands on wall, legs straight, looking over shoulder, 1boy",
        "doggy on couch armrest, torso folded, hips held, soft trembling thighs, 1boy",
        "prone bone, lying face down, pillow under hips, legs together, deep from behind, quiet moan, 1boy",
        "prone bone legs slightly open, face turned to side, flushed ear, sensual rear insertion, 1boy",
        "from behind kneeling hug, partner covering petite back, neck kisses, connected hips, 1boy",
        "standing doggy against desk, bent at waist, skirt still half on, looking back, 1boy",
        # ── spooning / side ──
        "spooning sex, side-lying, partner behind, leg lifted by hand, soft intimate insertion, 1boy",
        "spooning face near pillow, back arched into partner, hand holding his, cute sleepy lewd, 1boy",
        "side-lying facing each other, one leg hooked over hip, slow penetration, eye contact, 1boy",
        "side scissors-ish entry, legs intertwined, close bodies, soft grinding penetration, 1boy",
        # ── standing / lift / wall ──
        "standing sex, partner lifting petite girl, legs wrapped around waist, arms around neck, 1boy",
        "wall sex, back against wall, held up, legs locked, face close, heated breath, 1boy",
        "standing split-assist, one leg held high, facing partner, sensual stretch insertion, 1boy",
        "against window glass, chest pressed lightly, from behind standing, city night bokeh, 1boy",
        "counter height sitting sex, sitting on edge being entered, feet dangling then locked, 1boy",
        # ── seated / chair / lap ──
        "lap sitting face to face, straddling on chair, slow bounce, hugging, deep eye contact, 1boy",
        "chair reverse cowgirl, facing away on lap, hands on knees, looking back cute, 1boy",
        "sofa missionary-ish, half sitting reclined, legs open over partner, soft cushions, 1boy",
        "seiza style sit on lap, knees together-ish then open, traditional cute lewd seating, 1boy",
        # ── mating press soft (not extreme) ──
        "mating press soft, knees bent toward chest, partner covering body, forehead touch, deep but tender, 1boy",
        "mating press, ankles near shoulders, petite folded under partner, shy overwhelmed blush not ahegao, 1boy",
        "full body press missionary, chests together, slow deep, hands in hair, romantic lewd, 1boy",
        # ── amazon / woman on top variants ──
        "amazon position soft, partner on back legs up, girl leaning in control, cute dominant, 1boy",
        "woman on top lean-back, hands behind on bed, riding with arched torso, sensual silhouette, 1boy",
        # ── clothing still on insertion (arousal) ──
        "missionary with shirt still on, skirt pushed aside, panties to the side, clothed sex, cute contrast, 1boy",
        "doggy with hoodie still on, bottom half bare, looking back, casual lewd insertion, 1boy",
        "cowgirl in unbuttoned blouse, open chest, still wearing thigh-highs, riding, 1boy",
        "standing sex lifting school skirt, panties aside, uniform still worn, risky vibe, 1boy",
        "spooning with oversized sweater on, only lower body joined, cozy lewd, 1boy",
        # ── pace / tease insertion ──
        "slow insertion missionary, tip entering carefully, watching face for reaction, anticipatory blush, 1boy",
        "halfway penetration pause, cowgirl hovering, teasing both, biting lip, 1boy",
        "deep grind after full insertion, no big bounce, hip circles, intimate heat, 1boy",
        "pull-out almost then push back, missionary, teasing rhythm, soft gasp face, 1boy",
        # ── petite-focused ──
        "size difference missionary, petite under larger partner, careful thrusts, protected cute, 1boy",
        "petite cowgirl, small hips on partner, hands tiny on chest, looking down shyly proud, 1boy",
        "petite doggy, small frame arched, looking back with sparkle eyes, 1boy",
        "petite lifted standing sex, feet off floor, clinging tightly, 1boy",
    ]
    n_pose = uniq_extend(cb["pose"], poses)

    faces = [
        "soft bedroom eyes, glossy parted lips, heavy blush, cute aroused expression, looking at viewer",
        "shy pleasure blush, half-lidded eyes, slight open mouth, sensual but cute",
        "teary sparkle eyes from pleasure, biting lower lip, flustered cute face",
        "dazed happy blush, soft smile through pleasure, not exaggerated",
        "seductive eye contact during sex, gentle moan face, warm flush",
        "embarrassed aroused look, glancing away then back, pink cheeks",
        "lustful but cute gaze, wet eyes, soft O mouth, inviting",
        "pleasure frown cute, eyebrows tilted, trying to stay quiet, lips pressed then open",
        "kiss-ready parted lips, heavy eyelids, intimate sex face",
        "melting smile, eyes half closed from pleasure, adorable lewd",
        "upturned eyes looking at partner, trust and desire, soft blush",
        "cheek pressed to pillow, side face, flushed ear, quiet moan expression",
        "looking back over shoulder, seductive smile, doggy face charm",
        "looking down at connection shyly, then up with wet eyes, cowgirl face",
        "forehead sweat light, pleasure concentration, cute determined face",
        "afterglow soft smile, messy hair, satisfied blush, post-climax calm",
    ]
    n_face = uniq_extend(cb["face"], faces)

    jobs = [
        "missionary vaginal sex, slow deep thrusts, face to face, cute blush, eye contact, 1boy",
        "missionary vaginal penetration, legs wrapped, soft moaning, holding hands, 1boy",
        "cowgirl vaginal sex, hip grinding, girl on top, looking down with shy smile, 1boy",
        "reverse cowgirl vaginal sex, looking back, arched back, sensual bounce, 1boy",
        "doggy style vaginal sex, rear entry, looking back cute, hands gripping sheets, 1boy",
        "prone bone vaginal penetration, face down, pillow hug, soft moans, 1boy",
        "spooning vaginal sex, side entry, intimate cuddle thrusting, 1boy",
        "standing vaginal sex, lifted petite body, legs around waist, clinging, 1boy",
        "wall sex vaginal penetration, held against wall, close faces, heated breath, 1boy",
        "lap sitting vaginal sex, straddling chair, slow bounce, hug, 1boy",
        "mating press vaginal sex, folded legs, deep but tender, forehead touch, 1boy",
        "clothed missionary, panties aside, skirt up, shirt on, insertion, 1boy",
        "clothed doggy, hoodie on, bottom bare, rear insertion, 1boy",
        "cowgirl with thigh-highs still on, unbuttoned blouse, riding, 1boy",
        "slow vaginal insertion, watching reaction, anticipatory pleasure, 1boy",
        "deep grind vaginal sex after full insertion, hip circles, intimate, 1boy",
        "size difference vaginal missionary, careful pace, petite under partner, 1boy",
        "edge of bed missionary, hips lifted, rhythmic penetration, 1boy",
        "sofa cowgirl, cushions, quiet house vibe, sensual riding, 1boy",
        "against desk doggy, bent over, looking back, office-home lewd, 1boy",
    ]
    n_job = uniq_extend(cb["job"], jobs)

    details = [
        "connected hips, soft skin sheen, intimate body contact, sensual heat",
        "legs wrapped around partner waist, toes curled lightly from pleasure",
        "hands gripping sheets or shoulders, knuckles soft, aroused tension",
        "sweat on collarbone and nape, flushed chest, post-thrust glow",
        "panties pulled aside still on hip, clothing contrast during sex",
        "skirt bunched at waist, shirt half open, clothed sex detail",
        "petite belly lightly tensing with each thrust, small frame against partner",
        "wetness sheen at connection, tasteful not graphic, sensual implication",
    ]
    n_det = uniq_extend(cb["details"], details)

    BANKS.write_text(json.dumps(cb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"pose +{n_pose} total {len(cb['pose'])}")
    print(f"face +{n_face} total {len(cb['face'])}")
    print(f"job +{n_job} total {len(cb['job'])}")
    print(f"details +{n_det} total {len(cb['details'])}")
    print("ahegao remaining face", sum(1 for f in cb["face"] if "ahegao" in f.lower()))
    print("ahegao remaining pose", sum(1 for p in cb["pose"] if "ahegao" in p.lower()))


if __name__ == "__main__":
    main()
