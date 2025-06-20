collect_used_targets([], _, [], [], []).

%If unification works add to Middle
collect_used_targets([H|T], Targets, Left, [H|Middle], [MatchedTarget|Used]) :-
    member(MatchedTarget, Targets),
    H = MatchedTarget,
    collect_used_targets(T, Targets, Left, Middle, Used).

%Base case: add H to Left only when it cannot be matched OR when it matches
% with a target but (1) H contains variables and (2) it is not alpha-equivalent
% (structurally identical modulo variable renaming) to the target.
collect_used_targets([H|T], Targets, [H|Left], Middle, Used) :-
    (   \+ ( member(MatchedTarget, Targets),
             H = MatchedTarget )                           % no unification possible
    ;   ( member(MatchedTarget, Targets),                  % unifies…
          \+ variant(H, MatchedTarget),                    % …but not alpha-equivalent
          term_variables(H, Vars),
          Vars \= [] )                                     % …and contains variables
    ),
    collect_used_targets(T, Targets, Left, Middle, Used).

% match_partition(+Input, +Targets, -Left, -Middle, -Right)
match_partition(Input, Targets, Left, Middle, Right) :-
    collect_used_targets(Input, Targets, Left, Middle, Used),
    findall(T, (member(T, Targets), \+ memberchk(T, Used)), Right).
