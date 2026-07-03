"""Dramaturgy + canon gates — backtested on the real «Մոռացողը» failure (2026-07-03).

The pre-review state (secret only sketched, counter-idea a slogan, characters cost-free,
era changed at asset stage without upstream absorption) must FAIL the gate.
The post-review state (canon-secret.md written, Davit carries the counter-idea with a
tragic reason, Nare pays a price, era absorbed) must PASS.
"""
import json
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from lib.gatechain import run_story_gates  # noqa: E402
from lib import canon_guard  # noqa: E402


def _post_review_bible() -> dict:
    return {
        "premise": "Ընտանիքը 25 տարի թաքցնում է գաղտնիքը բոլորից՝ բացի նրանից, ով մոռանում է ամեն ինչ, ու նրանից, ում ոչ ոք չի հարցնում։",
        "controlling_idea": {
            "side_a": "Ջնջելով ցավը՝ ջնջում ես մարդուն։",
            "side_b": "Մոռանալը գթություն է։",
            "side_b_carrier": "Դավիթ",
            "side_b_tragic_reason": "Արամի հրաժեշտի նամակը ինքն է այրել. ճշմարտությունը հիմա ասելը նշանակում է հիվանդ հորն ասել, որ 25 տարի սխալ պատճառով է ցավել — և որ մեղավորը իր որդին է։",
        },
        "secret_chronology": {
            "file": "canon-secret.md",
            "what_happened": "1902-ի լուսաբացին վեճ որդու ապագայի շուրջ. Սուրենի «էս տնից գնացողը հետ չի գալիս» խոսքը, Արամի հեռացումը, ժամագործի ձեռքը կանգ առավ ժամացույցը լարելիս՝ 4:40։",
            "why_silent": "Դավիթը այրեց հրաժեշտի նամակը; երկու տղամարդու հայելային հպարտություն («թող ինքը կանչի»); պատերազմի տարիները «մահացել է» վարկածը դարձրին հավատալի ու հարմար։",
            "why_now": "Տատի մահով նամակները կտրվեցին, Սուրենի հիշողությունը քայքայվում է, և ֆինալում Նարեն է գրում առաջին «արի»-ն 25 տարում։",
            "who_knows_what_complete": True,
        },
        "characters": [
            {"name": "Սուրեն", "knows": "վեճը և իր խոսքը", "wrongly_believes": "որդին գնացել է առանց մի բառի",
             "cost": "կորցնում է հիշողությունը՝ պահելով միայն սպասումը. ամեն ընթրիք դատարկ ափսեով"},
            {"name": "Դավիթ", "knows": "վեճը և այրած նամակը", "wrongly_believes": "ճշմարտությունը կսպանի հորը",
             "cost": "25 տարվա ամոթ, ամուսնության մեջ լռության պատ, ֆինալում խոստովանության գին"},
            {"name": "Նարե", "knows": "ոչինչ, հետո՝ ամեն ինչ", "wrongly_believes": "ep5-ում՝ որ պապն է մեղավոր",
             "cost": "տետրը խլում են, հոր վստահությունը կորցնում է, ընտրում է շարունակել թաքուն"},
        ],
        "era": {"setting": "Իրական 1920-ականներ, «հիմա»=1927, Երևան", "absorbed": True},
    }


def test_post_review_canon_passes():
    r = run_story_gates(_post_review_bible())
    assert r["ok"], r["violations"]


def test_pre_review_state_fails_no_chronology():
    b = _post_review_bible()
    # The pre-review sketch: chronology not confirmed complete
    b["secret_chronology"]["who_knows_what_complete"] = False
    r = run_story_gates(b)
    assert not r["ok"]


def test_pre_review_state_fails_slogan_counter_idea():
    b = _post_review_bible()
    b["controlling_idea"]["side_b_tragic_reason"] = "գթություն է"  # slogan, no defensible reason
    r = run_story_gates(b)
    assert not r["ok"]


def test_pre_review_state_fails_costless_character():
    b = _post_review_bible()
    b["characters"][2]["cost"] = "ոչինչ"  # Nare as a tool, not a character
    r = run_story_gates(b)
    assert not r["ok"]


def test_era_not_absorbed_fails():
    b = _post_review_bible()
    b["era"]["absorbed"] = False  # the 1920s pivot living only in the look bible
    r = run_story_gates(b)
    assert not r["ok"]


def test_canon_guard_blocks_midpipeline_change(tmp_path):
    d = str(tmp_path)
    open(os.path.join(d, "look-bible.md"), "w").write("canon v1")
    open(os.path.join(d, "canon-secret.md"), "w").write("secret v1")
    canon_guard.lock(d)
    # era pivot at asset stage — exactly the Moratsoghy case
    open(os.path.join(d, "look-bible.md"), "w").write("canon v2 (1920s pivot)")
    r = canon_guard.check(d, "asset")
    assert not r["ok"] and "look-bible.md" in r["changed"]
    # same change during the script stage is free
    assert canon_guard.check(d, "script")["ok"]
    # writing a re-validation note unblocks
    time.sleep(0.05)
    open(os.path.join(d, canon_guard.REVALIDATION), "w").write("re-checked premise/dialogue/era math")
    assert canon_guard.check(d, "asset")["ok"]


def test_canon_guard_stale_revalidation_still_blocks(tmp_path):
    d = str(tmp_path)
    open(os.path.join(d, "look-bible.md"), "w").write("v1")
    canon_guard.lock(d)
    open(os.path.join(d, canon_guard.REVALIDATION), "w").write("old note")
    time.sleep(0.05)
    open(os.path.join(d, "look-bible.md"), "w").write("v2 changed AFTER the note")
    r = canon_guard.check(d, "asset")
    assert not r["ok"]
