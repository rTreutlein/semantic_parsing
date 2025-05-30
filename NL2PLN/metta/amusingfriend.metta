!(import! &self compiler)

!(bind! &kb (init-kb))

;;Honesty

!(compileAdd &kb (: honest (Honest $person) (STV 0.8 0.9)))

!(compileAdd &kb (: toldTruthAbout (ToldTruthAbout $a $b $c) (STV 0.00001 0.7)))

!(compileAdd &kb (: (toldTruthAbout honest) (Implication (ToldTruthAbout $a $b $c) (Honest $a)) (STV 1.0 1.0)))

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

!(compileAdd &kb (: (friends honest) (Implication (Friends $a $b) (And (Honest $a) (Honest $b))) (STV 0.85 0.5)))

;;Being Funny

!(compileAdd &kb (: toldjoke (ToldJoke $a) (STV 0.000001 0.6)))

!(compileAdd &kb (: isfunny (IsFunny $a) (STV 0.69 0.7)))

!(compileAdd &kb (: (toldjoke isfunny) (Implication (ToldJoke $a) (IsFunny $a)) (STV 0.000001 0.6)))

!(compileAdd &kb (: (funny amusing) (Equivalence (IsFunny $a) (Amusing $a)) (STV 0.7 0.9)))

;; The Party

!(compileAdd &kb (: BobToldTheTruthToJillAboutThePary (ToldTruthAbout bob jill party) (STV 1.0 1.0)))

!(compileAdd &kb (: BobToldAJoke (ToldJoke bob) (STV 1.0 1.0))) ;Simplified from told joke to jima at party

;!(show-cs &kb)

;!(query &kb (fromNumber 2) (: $prf (And (Honest self) (Honest bob)) $tv))

!(time (query &kb (fromNumber 3) (: $prf (Friends self bob) $tv)))

;Depth 2:
;(Time 68.85777831077576 (() ⊢ ((: (revision ((inverted (friends honest) (revision (AcquaintedToFriends humanAquanted) friends) (revision ((friends honest) friends) (conjunction honest honest))) (conjunction (honest self) honest)) (AcquaintedToFriends (revision (conjunction SelfHumane BobHuman SelfKnowBob) humanAquanted))) (Friends self bob) (STV 0.054553013636602775 0.6451612903225806)))))

;Depth3:
;(Time 159.6881182193756 (() ⊢ ((: (AcquaintedToFriends (conjunction (revision (proj humanAquanted) SelfHumane) (revision (proj humanAquanted) BobHuman) SelfKnowBob)) (Friends self bob) (STV 0.0982472875805841 0.5)))))

;Depth4
;(Time 356.3314516544342 (() ⊢ ((: (AcquaintedToFriends (conjunction (revision (proj humanAquanted) SelfHumane) (revision (proj humanAquanted) BobHuman) SelfKnowBob)) (Friends self bob) (STV 0.0982472875805841 0.5)))))

;Things done

;Loop Prevention
;Early mearging of conclusions
;Update to 0.2.5
;Extension of Rule Compiler
