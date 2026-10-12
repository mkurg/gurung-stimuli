form Simplify trigger labels without changing annotations
    sentence Input_grid
    sentence Output_grid
endform

Read from file: input_grid$
original = selected("TextGrid")
numberOfTiers = Get number of tiers
triggerTier = 0
for tier from 1 to numberOfTiers
    name$ = Get tier name: tier
    if name$ = "triggers"
        triggerTier = tier
    endif
endfor
if triggerTier = 0
    exitScript: "No triggers tier found."
endif
Copy: "compact_codes"
compact = selected("TextGrid")
pointCount = Get number of points: triggerTier
for point from 1 to pointCount
    label$ = Get label of point: triggerTier, point
    if index(label$, "Stimulus/S") > 0
        clean$ = replace_regex$(label$, "Mk[0-9]+: Stimulus/S[ ]*", "S ", 0)
    else
        if index_regex(label$, "^S[ ]*[0-9]+") > 0
            clean$ = replace_regex$(label$, "S[ ]+", "S ", 0)
        else
            clean$ = ""
        endif
    endif
    Set point text: triggerTier, point, clean$
endfor
Save as text file: output_grid$

# Read the saved file back and compare every unaffected tier and timestamp.
Read from file: output_grid$
saved = selected("TextGrid")
savedTierCount = Get number of tiers
assert savedTierCount = numberOfTiers
for tier from 1 to numberOfTiers
    selectObject: original
    tierName$ = Get tier name: tier
    isInterval = Is interval tier: tier
    selectObject: saved
    savedName$ = Get tier name: tier
    savedIsInterval = Is interval tier: tier
    assert savedName$ = tierName$
    assert savedIsInterval = isInterval
    if isInterval
        selectObject: original
        count = Get number of intervals: tier
        selectObject: saved
        savedCount = Get number of intervals: tier
        assert savedCount = count
        for interval from 1 to count
            selectObject: original
            start = Get start time of interval: tier, interval
            finish = Get end time of interval: tier, interval
            text$ = Get label of interval: tier, interval
            selectObject: saved
            savedStart = Get start time of interval: tier, interval
            savedFinish = Get end time of interval: tier, interval
            savedText$ = Get label of interval: tier, interval
            assert savedStart = start
            assert savedFinish = finish
            assert savedText$ = text$
        endfor
    else
        selectObject: original
        count = Get number of points: tier
        selectObject: saved
        savedCount = Get number of points: tier
        assert savedCount = count
        for point from 1 to count
            selectObject: original
            time = Get time of point: tier, point
            text$ = Get label of point: tier, point
            selectObject: saved
            savedTime = Get time of point: tier, point
            savedText$ = Get label of point: tier, point
            assert savedTime = time
            if tier <> triggerTier
                assert savedText$ = text$
            endif
        endfor
    endif
endfor
writeInfoLine: "PASS: all tiers, times and manual annotations preserved; ", pointCount, " trigger labels simplified."
