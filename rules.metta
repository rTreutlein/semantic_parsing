
!(add-atom &kb (: ModusPonens
                (-> (→ $p $q)           ; Premise 1
                    (-> $p              ; Premise 2
                        $q))))          ; Conclusion

; Hypothetical Syllogism
!(add-atom &kb (: HypotheticalSyllogism
                (-> (→ $p $q)           ; Premise 1
                    (-> (→ $q $r)       ; Premise 2
                        (→ $p $r)))))   ; Conclusion

; Disjunctive Syllogism
!(add-atom &kb (: DisjunctiveSyllogism
                (-> (∨ $p $q)           ; Premise 1
                    (-> (¬ $p)          ; Premise 2
                        $q))))          ; Conclusion

; Conjunction Introduction
!(add-atom &kb (: ConjunctionIntroduction
                (-> $p                  ; Premise 1
                    (-> $q              ; Premise 2
                        (∧ $p $q)))))   ; Conclusion

; Conjunction Elimination (Left and Right)
!(add-atom &kb (: ConjunctionEliminationLeft
                (-> (∧ $p $q)           ; Premise
                    $p)))               ; Conclusion

!(add-atom &kb (: ConjunctionEliminationRight
                (-> (∧ $p $q)           ; Premise
                    $q)))               ; Conclusion

; Disjunction Introduction (Left and Right)
!(add-atom &kb (: DisjunctionIntroductionLeft
                (-> $p                  ; Premise
                    (∨ $p $q))))        ; Conclusion

!(add-atom &kb (: DisjunctionIntroductionRight
                (-> $q                  ; Premise
                    (∨ $p $q))))        ; Conclusion


