collect_used_targets([], _, [], [], []).
collect_used_targets([H|T], Targets, Left, [H|Middle], [MatchedTarget|Used]) :-
    member(MatchedTarget, Targets),
    H = MatchedTarget,
    collect_used_targets(T, Targets, Left, Middle, Used).
collect_used_targets([H|T], Targets, [H|Left], Middle, Used) :-
    %\+ (member(Target, Targets), H = Target),
    collect_used_targets(T, Targets, Left, Middle, Used).

% match_partition(+Input, +Targets, -Left, -Middle, -Right)
match_partition(Input, Targets, Left, Middle, Right) :-
    collect_used_targets(Input, Targets, Left, Middle, Used),
    findall(T, (member(T, Targets), \+ memberchk(T, Used)), Right).
