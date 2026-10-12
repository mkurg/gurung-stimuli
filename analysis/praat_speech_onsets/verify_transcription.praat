form: "Verify transcription tier"
    sentence: "Source file", ""
    sentence: "Updated file", ""
endform

source = Read from file: source_file$
sourceTiers = Get number of tiers
assert sourceTiers = 2
duration = Get end time

updated = Read from file: updated_file$
updatedTiers = Get number of tiers
assert updatedTiers = 3
updatedDuration = Get end time
assert updatedDuration = duration

for tier from 1 to 2
    selectObject: source
    sourceName$ = Get tier name: tier
    sourceCount = Get number of points: tier
    selectObject: updated
    updatedName$ = Get tier name: tier
    updatedCount = Get number of points: tier
    assert sourceName$ = updatedName$
    assert sourceCount = updatedCount
    for point from 1 to sourceCount
        selectObject: source
        sourceTime = Get time of point: tier, point
        sourceLabel$ = Get label of point: tier, point
        selectObject: updated
        updatedTime = Get time of point: tier, point
        updatedLabel$ = Get label of point: tier, point
        assert sourceTime = updatedTime
        assert sourceLabel$ = updatedLabel$
    endfor
endfor

selectObject: updated
tierName$ = Get tier name: 3
assert tierName$ = "transcription"
intervalCount = Get number of intervals: 3
assert intervalCount = 1
intervalStart = Get start time of interval: 3, 1
intervalEnd = Get end time of interval: 3, 1
intervalLabel$ = Get label of interval: 3, 1
assert intervalStart = 0
assert intervalEnd = duration
assert intervalLabel$ = ""
writeInfoLine: "PASS: transcription interval tier added; original tiers and all points preserved."
