#!/usr/bin/bash

# Run time: ~30 min (8-core parallel)

set -e

# 0. Extract articles with superscript and subscript issues
date
echo "Starting superscript/subscript extraction"
../venv/bin/python3 ../dump_grep_regex.py '(<sub>|<sup>|¹|²|³|⁴|⁵|⁶|⁷|⁸|⁹|⁰|ⁱ|⁺|⁻|⁼|⁽⁾|ᵃ|ᵇ|ᶜ|ᵈ|ᵉ|ᶠ|ᵍ|ʰ|ⁱ|ʲ|ᵏ|ˡ|ᵐ|ⁿ|ᵒ|ᵖ|ʳ|ˢ|ᵗ|ᵘ|ᵛ|ʷ|ˣ|ʸ|ᶻ|ᴬ|ᴮ|ᴰ|ᴱ|ᴳ|ᴴ|ᴵ|ᴶ|ᴷ|ᴸ|ᴹ|ᴺ|ᴼ|ᴾ|ᴿ|ᵀ|ᵁ|ⱽ|ᵂ|₀|₁|₂|₃|₄|₅|₆|₇|₈|₉|₊|₋|₌|₍₎|ₐ|ₑ|ₕ|ᵢ|ⱼ|ₖ|ₗ|ₘ|ₙ|ₒ|ₚ|ᵣ|ₛ|ₜ|ᵤ|ᵥ|ₓ|ꟹ|ᵝ|ᵞ|ᵟ|ᵋ|ᶿ|ᶥ|ᶹ|ᵠ|ᵡ|ᵦ|ᵧ|ᵨ|ᵩ|ᵪ|ᵅ|ᶜ̧|ᶞ|ᵊ|ᶪ|ᶴ|ᶵ|ꭩ|ˀ|ₔ|ᵑ)' > /var/local/moss/bulk-wikipedia/super-sub-dump.xml
# Run time: 1.5h
# Reduction factor: 77G to 4.6G

# 1. Complete revert and verify which symbols in IPA templates can
# stay as HTML
date
echo "Starting revert candidate greps"
cat /var/local/moss/bulk-wikipedia/super-sub-dump.xml | ../venv/bin/python3 ../dump_grep_inline.py '{{([Aa]ngbr )?IPA[^}]+<su[pb]' > revert-candidates-ipa.txt
# Run time: 5 min

# 2. Same for Proto-Indo-European
date
cat /var/local/moss/bulk-wikipedia/super-sub-dump.xml | ../venv/bin/python3 ../dump_grep_inline.py '{{PIE[^}]+<su[pb]' > revert-candidates-pie.txt
date
# Run time: 5 min

# 3. Find Unicode superscripts and subscripts that:
#  A.) have nothing to do with linguistics and should be changed
#  B.) have a linguistics template but should be changed to HTML
#  C.) should stay as Unicode and need a linguistics template
#  D.) should be changed to HTML and need a linguistics template

# Step 3 triage with only less-common characters:
date
cat /var/local/moss/bulk-wikipedia/super-sub-dump.xml | ../venv/bin/python3 ../dump_grep_inline.py '(⁴|⁵|⁶|⁷|⁸|⁹|⁰|ⁱ|⁺|⁻|⁼|⁽⁾|ᵃ|ᵇ|ᶜ|ᵈ|ᵉ|ᶠ|ᵍ|ⁱ|ᵏ|ˡ|ᵐ|ᵒ|ᵖ|ʳ|ˢ|ᵗ|ᵘ|ᵛ|ˣ|ʸ|ᶻ|ᴬ|ᴮ|ᴰ|ᴱ|ᴳ|ᴴ|ᴵ|ᴶ|ᴷ|ᴸ|ᴹ|ᴺ|ᴼ|ᴾ|ᴿ|ᵀ|ᵁ|ⱽ|ᵂ|₀|₁|₂|₃|₄|₅|₆|₇|₈|₉|₊|₋|₌|₍₎|ₐ|ₑ|ₕ|ᵢ|ⱼ|ₖ|ₗ|ₘ|ₙ|ₒ|ₚ|ᵣ|ₛ|ₜ|ᵤ|ᵥ|ₓ|ꟹ|ᵝ|ᵞ|ᵟ|ᵋ|ᶿ|ᶥ|ᶹ|ᵠ|ᵡ|ᵦ|ᵧ|ᵨ|ᵩ|ᵪ|ᵅ|ᶜ̧|ᶞ|ᵊ|ᶪ|ᶴ|ᶵ|ꭩ|ˀ|ₔ|ᵑ)' | grep -v '{{IPA' | grep -v '{{angbr IPA' | grep -v '{{PIE' | grep -v '{{7seg' | grep -v '\[\[File:' | grep -v '\[\[Image:' | grep -vP 'ipa symbol\d\=' > super-sub-sortme.txt

# Step 3 with all characters:
# cat /var/local/moss/bulk-wikipedia/super-sub-dump.xml | ../venv/bin/python3 ../dump_grep_inline.py '(¹|²|³|⁴|⁵|⁶|⁷|⁸|⁹|⁰|ⁱ|⁺|⁻|⁼|⁽⁾|ᵃ|ᵇ|ᶜ|ᵈ|ᵉ|ᶠ|ᵍ|ʰ|ⁱ|ʲ|ᵏ|ˡ|ᵐ|ⁿ|ᵒ|ᵖ|ʳ|ˢ|ᵗ|ᵘ|ᵛ|ʷ|ˣ|ʸ|ᶻ|ᴬ|ᴮ|ᴰ|ᴱ|ᴳ|ᴴ|ᴵ|ᴶ|ᴷ|ᴸ|ᴹ|ᴺ|ᴼ|ᴾ|ᴿ|ᵀ|ᵁ|ⱽ|ᵂ|₀|₁|₂|₃|₄|₅|₆|₇|₈|₉|₊|₋|₌|₍₎|ₐ|ₑ|ₕ|ᵢ|ⱼ|ₖ|ₗ|ₘ|ₙ|ₒ|ₚ|ᵣ|ₛ|ₜ|ᵤ|ᵥ|ₓ|ꟹ|ᵝ|ᵞ|ᵟ|ᵋ|ᶿ|ᶥ|ᶹ|ᵠ|ᵡ|ᵦ|ᵧ|ᵨ|ᵩ|ᵪ|ᵅ|ᶜ̧|ᶞ|ᵊ|ᶪ|ᶴ|ᶵ|ꭩ|ˀ|ₔ|ᵑ)' | grep -v '{{IPA' | grep -v '{{angbr IPA' | grep -v '{{PIE' | grep -v '{{7seg' | grep -v '\[\[File:' | grep -v '\[\[Image:' | grep -vP 'ipa symbol\d\=' > super-sub-sortme.txt
# OR look at tmp-entities.txt and start from the least-common superscripts/subscripts

date
sort super-sub-sortme.txt > super-sub-sorted.txt
date
cat super-sub-sorted.txt | perl -pe 's/(^.*?):.*$/$1/' | uniq > super-sub-titles.txt


# A.) have nothing to do with linguistics and should be changed
cat super-sub-titles.txt | grep -v language | grep -v dialect | grep -v creole | grep -v Proto | grep -v Schwa | grep -v verb | grep -v Chinese | grep -v people | grep -v deity | grep -v god | grep -v Arabic | grep -vP "'[^st]" | grep -v Voiced | grep -vi palatal | grep -vP '^\w$' > super-sub-jwb-non-linguistics.txt

# B.) have a linguistics template but should be changed to HTML

grep '{{lang' super-sub-sorted.txt > super-sub-tl-lang-audit.txt

# C.) should stay as Unicode and need a linguistics template
# D.) should be changed to HTML and need a linguistics template

# [[Tone letter]]
# [[Classical Japanese]]:
#  {{IPA|hɑ'''n'''<sup>H</sup>d͡zɨ<sup>H</sup>}})
cat super-sub-sorted.txt |grep -P 'languages?:' > super-sub-languages-audit.txt

echo "Superscript/subscript audit complete."
