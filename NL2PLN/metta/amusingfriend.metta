
!(pragma! exec skip)

!(import! &self compiler)

!(pragma! exec true)

!(bind! &kb (init-kb))

;;Honesty

!(compileAdd &kb (: honest (Honest $person) (STV 0.8 0.9)))

!(compileAdd &kb (: toldTruthAbout (ToldTruthAbout $a $b $c) (STV 0.00001 0.7)))

!(compileAdd &kb (: toldTruthAbout_i_honest (Implication (ToldTruthAbout $a $b $c) (Honest $a)) (STV 1.0 1.0)))

;; Humanity

!(compileAdd &kb (: humanAquanted (And (Human $a) (Human $b) (Acquainted $a $b)) (STV 0.0002 0.9)))

;; Bob

!(compileAdd &kb (: BobHuman (Human bob) (STV 1.0 1.0)))

;; Self

!(compileAdd &kb (: SelfHumane (Human self) (STV 1.0 1.0)))

!(compileAdd &kb (: (honest self) (Honest self) (STV 0.9 0.9)))

!(compileAdd &kb (: SelfKnowBob (Acquainted self bob) (STV 1.0 1.0)))

;; Friendship

!(compileAdd &kb (: friends (Friends $person $person) (STV 0.0001 0.9)))

!(compileAdd &kb (: friendship (Equivalence (Friends $a $b) (Friends $b $a)) (STV 1.0 1.0)))

!(compileAdd &kb (: AcquaintedToFriends (Implication (And (Human $a) (Human $b) (Acquainted $a $b)) (Friends $a $b)) (STV 0.1 0.5)))

!(compileAdd &kb (: friends_i_honest (Implication (Friends $a $b) (And (Honest $a) (Honest $b))) (STV 0.85 0.5)))

;;Being Funny

!(compileAdd &kb (: toldjoke (ToldJoke $a) (STV 0.000001 0.6)))

!(compileAdd &kb (: isfunny (IsFunny $a) (STV 0.69 0.7)))

!(compileAdd &kb (: toldjoke_i_isfunny (Implication (ToldJoke $a) (IsFunny $a)) (STV 0.000001 0.6)))

!(compileAdd &kb (: funny_i_amusing (Equivalence (IsFunny $a) (Amusing $a)) (STV 0.7 0.9)))

;; The Party

!(compileAdd &kb (: BobToldTheTruthToJillAboutThePary (ToldTruthAbout bob jill party) (STV 1.0 1.0)))

!(compileAdd &kb (: BobToldAJoke (ToldJoke bob) (STV 1.0 1.0))) ;Simplified from told joke to jima at party

!(show-cs &kb)

;!(mtime (query &kb (fromNumber 1) (: $prf (And (Human self) (Human bob) (Acquainted self bob)) $tv)))

;!(mtime (query &kb (fromNumber 2) (: ((inverted (friends honest) $a $b) $c) (Friends self bob) $tv)))
;!(mtime (query &kb (fromNumber 3) (: ((inverted (friends honest) $a $b) $c) (Friends self bob) $tv)))
!(mtime (query &kb (fromNumber 3) (: $prf (Friends self bob) $tv)))

;Depth 2:
;(Time 91.18175387382507 (() |- ((: (revision (AcquaintedToFriends (revision humanAquanted (conjunction SelfHumane BobHuman SelfKnowBob))) ((inverted (friends honest) (revision friends (AcquaintedToFriends humanAquanted)) (revision (conjunction honest honest) ((friends honest) friends))) (conjunction (honest self) honest))) (Friends self bob) (STV 0.05499454125192756 0.6451612903225806)))))
;(Time 34.36517882347107 (() |- ((: (revision (AcquaintedToFriends (revision humanAquanted (conjunction SelfHumane BobHuman SelfKnowBob))) ((inverted (friends honest) (revision friends (AcquaintedToFriends humanAquanted)) (revision ((friends honest) friends) (conjunction honest honest))) (conjunction (honest self) honest))) (Friends self bob) (STV 0.05499454125192756 0.6451612903225806)))))

;Depth3:
;(Time 243.3953709602356  (() |- ((: (revision (AcquaintedToFriends (conjunction (revision (revision SelfHumane (proj 1.0 humanAquanted)) (proj 0 humanAquanted)) (revision (revision BobHuman (proj 1.0 humanAquanted)) (proj 0 humanAquanted)) SelfKnowBob)) ((inverted (friends honest) (revision friends (AcquaintedToFriends humanAquanted)) (revision (conjunction ((toldTruthAbout honest) toldTruthAbout) ((toldTruthAbout honest) toldTruthAbout)) ((friends honest) (revision friends (AcquaintedToFriends humanAquanted))))) (conjunction (revision (honest self) ((toldTruthAbout honest) toldTruthAbout)) (revision ((toldTruthAbout honest) toldTruthAbout) ((toldTruthAbout honest) BobToldTheTruthToJillAboutThePary))))) (Friends self bob) (STV 0.16244889021251788 0.6451612315871008)))))
;(Time 264.48182797431946 (() |- ((: (revision (AcquaintedToFriends (conjunction (revision (revision SelfHumane (proj 1.0 humanAquanted)) (proj 0 humanAquanted)) (revision (revision BobHuman (proj 1.0 humanAquanted)) (proj 0 humanAquanted)) SelfKnowBob)) ((inverted (friends honest) (revision friends (AcquaintedToFriends humanAquanted)) (revision (conjunction ((toldTruthAbout honest) toldTruthAbout) ((toldTruthAbout honest) toldTruthAbout)) ((friends honest) (revision friends (AcquaintedToFriends humanAquanted))))) (conjunction (revision (honest self) ((toldTruthAbout honest) toldTruthAbout)) (revision ((toldTruthAbout honest) toldTruthAbout) ((toldTruthAbout honest) BobToldTheTruthToJillAboutThePary))))) (Friends self bob) (STV 0.16244889021251788 0.6451612315871008)))))

;[(Time 77.62711119651794 ((() |- ((: (revision (AcquaintedToFriends (conjunction (revision (revision (proj 0 humanAquanted) (proj 1 humanAquanted)) SelfHumane) (revision (revision (proj 0 humanAquanted) (proj 1 humanAquanted)) BobHuman) SelfKnowBob)) ((inverted friends_i_honest (revision friends (AcquaintedToFriends humanAquanted)) (revision (friends_i_honest (revision friends (AcquaintedToFriends humanAquanted))) (conjunction (revision honest (toldTruthAbout_i_honest toldTruthAbout)) (revision honest (toldTruthAbout_i_honest toldTruthAbout))))) (conjunction (revision (revision honest (toldTruthAbout_i_honest toldTruthAbout)) (honest self)) (revision honest (toldTruthAbout_i_honest toldTruthAbout))))) (Friends self bob) (STV 0.05494793218485973 0.6451612903225806))))))]
;[(Time 85.03461050987244 ((() |- ((: (revision (AcquaintedToFriends (conjunction (revision (revision (proj 0 humanAquanted) (proj 1 humanAquanted)) SelfHumane) (revision (revision (proj 0 humanAquanted) (proj 1 humanAquanted)) BobHuman) SelfKnowBob)) ((inverted friends_i_honest (revision friends (AcquaintedToFriends humanAquanted)) (revision (friends_i_honest (revision friends (AcquaintedToFriends humanAquanted))) (conjunction (revision honest (toldTruthAbout_i_honest toldTruthAbout)) (revision honest (toldTruthAbout_i_honest toldTruthAbout))))) (conjunction (revision (revision honest (toldTruthAbout_i_honest toldTruthAbout)) (honest self)) (revision honest (toldTruthAbout_i_honest toldTruthAbout))))) (Friends self bob) (STV 0.05494793218485973 0.6451612903225806))))))]

;Depth4
;(Time 356.3314516544342 (() |- ((: (AcquaintedToFriends (conjunction (revision (proj humanAquanted) SelfHumane) (revision (proj humanAquanted) BobHuman) SelfKnowBob)) (Friends self bob) (STV 0.0982472875805841 0.5)))))

;Things done

;Loop Prevention
;Early mearging of conclusions
;Update to 0.2.5
;Extension of Rule Compiler
